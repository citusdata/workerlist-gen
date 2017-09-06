import time
import docker
import psycopg2
import json
import os

def connect_to_db():
    conn = None
    a = 0
    while a < 10 and conn is None:
        time.sleep(2)
        try:
            conn = psycopg2.connect("dbname='postgres' user='postgres' host='citus_master' password=''")
        except:
            print("I am unable to connect")
            a = a + 1
    return conn

def add_workers(conn, workers):
    for worker in workers:
        add_worker(conn, worker, 5432)
    conn.commit()


def add_worker(conn, host, port):
    cur = conn.cursor()
    worker_dict = ({"host": host, "port": port})
    try:
        cur.execute("""SELECT master_add_node(%(host)s, %(port)s)""", worker_dict)
    except:
        print("I can't add worker to the coordinator!")


def remove_worker(conn, host, port):
    cur = conn.cursor()
    worker_dict = ({"host": host, "port": port})
    try:
        cur.execute("""SELECT master_remove_node(%(host)s, %(port)s)""", worker_dict)
    except:
        print("I can't remove worker from the coordinator!")


def docker_checker():

    end_point = "unix:///var/run/docker.sock"
    client = docker.APIClient(base_url=end_point)
    master_found = False
    worker_set = set()
    conn = None
    for event in client.events():
        event_jsons = [json.loads(i) for i in event.split('\n') if i != '']

        for each_event in event_jsons:
            if 'status' in each_event and each_event['status'] == "start":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master":
                    master_found = True
                    conn = connect_to_db()
                    add_workers(conn, worker_set)

                if master_found and service_name == "worker":
                    add_worker(conn, name, 5432)
                    conn.commit()
                elif master_found is False:
                    worker_set.add(name)
            elif 'status' in each_event and each_event['status'] == "die":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master":
                    master_found = False
                    conn = None
                    worker_set = set()

                if master_found and service_name == "worker":
                    remove_worker(conn, name, 5432)
                    conn.commit()


def main():
    docker_checker()


if __name__ == "__main__":
    main()

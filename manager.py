import time
import docker
import psycopg2
import json


def connect_to_db():
    conn = None
    while conn is None:
        time.sleep(1)
        try:
            conn = psycopg2.connect("dbname='postgres' user='postgres' host='/var/run/postgresql' password=''")
        except Exception, e:
            print("Failed to connect to db: " + str(e))
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
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    master_found = False
    worker_set = set()
    conn = None
    print("HELLOOOOOOOOOOOOOOOOOOOOO")
    for event in client.events():
        event_jsons = [json.loads(i) for i in event.split('\n') if i != '']

        for each_event in event_jsons:
            if 'status' in each_event and each_event['status'] == "start":
                if 'com.docker.compose.service' in each_event['Actor']['Attributes']:
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
                if 'com.docker.compose.service' in each_event['Actor']['Attributes']:
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
    print("ENTERED!\n")
    docker_checker()


if __name__ == "__main__":
    main()

import docker
import psycopg2
import json
import time


def get_env_vars(client):
    global postgres_user
    global postgres_pass
    global postgres_db

    container = client.containers.get("citus_master")
    env_vars = container.exec_run(cmd='env')

    for each_line in env_vars.splitlines():
        if 'POSTGRES' in each_line:
            (key, val) = each_line.split("=")
            if key == "POSTGRES_USER":
                postgres_user = val
            elif key == "POSTGRES_PASSWORD":
                postgres_pass = val
            elif key == "POSTGRES_DB":
                postgres_db = val


def connect_to_db(client):
    conn = None
    a = 0

    get_env_vars(client)

    while a < 10 and conn is None:
        time.sleep(2)
        try:
            conn = psycopg2.connect("dbname=%s user=%s host=%s password=%s" %
                                    (postgres_db, postgres_user, "citus_master", postgres_pass))
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


def get_workers(conn):
    cur = conn.cursor()
    workers = None

    try:
        cur.execute("""SELECT master_get_active_worker_nodes()""")
        workers = cur.fetchall()
    except:
        print("I can't fetch active workers!")

    return workers


def check_cluster(client):
    containers = client.containers.list()
    conn = None
    worker_set = set()
    workers = set()
    for container in containers:
        if container.name == 'citus_master':
            conn = connect_to_db(client)
            workers = get_workers(conn)
        elif 'citus_worker' in container.name:
            worker_set.add(container.name)

    for each_worker in workers:
        (worker_name, port) = each_worker[0].split(',')
        if worker_name[1:] not in worker_set:
            remove_worker(conn, worker_name[1:], port[:len(port) - 1])

    if conn is not None:
        add_workers(conn, worker_set)

    print(worker_set)

    return conn, worker_set


def docker_checker():
    end_point = "unix:///var/run/docker.sock"
    client = docker.DockerClient(base_url=end_point)
    worker_set = set()

    (conn, worker_set) = check_cluster(client)

    for event in client.events():
        event_jsons = [json.loads(i) for i in event.split('\n') if i != '']

        for each_event in event_jsons:
            if 'status' in each_event and each_event['status'] == "start":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master" and conn is None:
                    conn = connect_to_db(client)
                    add_workers(conn, worker_set)

                if service_name == "worker" and conn is not None:
                    add_worker(conn, name, 5432)
                    conn.commit()

                if service_name == "worker" and conn is None:
                    worker_set.add(name)
            elif 'status' in each_event and each_event['status'] == "die":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master":
                    conn = None
                    worker_set = set()

                if service_name == "worker" and conn is not None:
                    remove_worker(conn, name, 5432)
                    conn.commit()


def main():
    docker_checker()


if __name__ == "__main__":
    main()

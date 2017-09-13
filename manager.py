# ----------------------------------------------------------------------------------------
#
# manager.py
#
# Created to manage add/remove worker operations in Citus docker-compose.
#
# ----------------------------------------------------------------------------------------
import docker
import psycopg2
import json


# gets the environment variables from master to connect to database.
def get_env_vars(client):
    global postgres_user
    global postgres_pass
    global postgres_db

    container = client.containers.get("citus_master")

    env_vars = (container.exec_run(cmd='env')).decode('utf-8')

    for each_line in env_vars.split('\n'):
        if 'POSTGRES' in each_line:
            (key, val) = each_line.split("=")
            if key == "POSTGRES_USER":
                postgres_user = val
            elif key == "POSTGRES_PASSWORD":
                postgres_pass = val
            elif key == "POSTGRES_DB":
                postgres_db = val


# adds the worker container's host and port information to master
def add_worker(conn, host, port):
    cur = conn.cursor()
    worker_dict = ({"host": host, "port": port})

    try:
        cur.execute("""SELECT master_add_node(%(host)s, %(port)s)""", worker_dict)
    except:
        print("I can't add worker to the coordinator!")

# removes the worker container's host and port information from master
def remove_worker(conn, host, port):
    cur = conn.cursor()
    worker_dict = ({"host": host, "port": port})
    try:
        cur.execute("""SELECT master_remove_node(%(host)s, %(port)s)""", worker_dict)
    except:
        print("I can't remove worker from the coordinator!")


# connect_to_master method is used to connect to master coordinator at the start-up.
# Citus docker-compose has a dependency mapping as worker -> manager -> master.
# This means that whenever manager is created, master is already there. If it is healthy,
# we can connect to it. If not, just returns None.
def connect_to_master(client):
    containers = client.containers.list()
    conn = None

    # inspect_container method is only provided for APIClient
    client_API = docker.APIClient(base_url=end_point)

    # for each current containers, checks if they are master and healthy
    for container in containers:
        c_name = container.name
        service_label = container.labels['com.docker.compose.service']
        status = client_API.inspect_container(c_name)
        if 'Health' in status['State'] and service_label == 'master':

            health_status = status['State']['Health']['Status']
            if health_status == 'healthy':

                # fetches the necessary variables to be able to connect to the database
                get_env_vars(client)

                # the container is both master and healthy, so just connect to it
                try:
                    conn = psycopg2.connect("dbname=%s user=%s host=%s password=%s" %
                                            (postgres_db, postgres_user, c_name, postgres_pass))
                except:
                    print("I am unable to connect to the master")

    return conn


def docker_checker():
    global end_point
    end_point = "unix:///var/run/docker.sock"
    client = docker.DockerClient(base_url=end_point)

    # creates the necessary connection to make the sql calls if the master is ready
    conn = connect_to_master(client)

    # client.events() is a generator.
    # This is an infinite loop listening to the docker events.
    for event in client.events():

        # Sometimes, multiple events might come wrapped in the same event
        event_jsons = [json.loads(i) for i in event.splitlines() if i != '']

        for each_event in event_jsons:

            if 'status' in each_event and each_event['status'] == "health_status: healthy":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master" and conn is None:
                    get_env_vars(client)

                    try:
                        conn = psycopg2.connect("dbname=%s user=%s host=%s password=%s" %
                                                (postgres_db, postgres_user, name, postgres_pass))
                    except:
                        print("I am unable to connect")

                if service_name == "worker" and conn is not None:
                    add_worker(conn, name, 5432)
                    conn.commit()

            elif 'status' in each_event and each_event['status'] == "die":
                service_name = each_event['Actor']['Attributes']['com.docker.compose.service']
                name = each_event['Actor']['Attributes']['name']

                if service_name == "master":
                    conn = None

                if service_name == "worker" and conn is not None:
                    remove_worker(conn, name, 5432)
                    conn.commit()


def main():
    docker_checker()


if __name__ == "__main__":
    main()

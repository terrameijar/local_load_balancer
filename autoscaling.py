import time
import docker

target_cpu_load = 30  # 30%
min_cpu_load = 10  # 10%
min_containers = 1
max_containers = 3
cooldown_time_end = 0
low_cpu_count = 0


client = docker.from_env()


def get_running_containers():
    containers = client.containers.list(filters={"name": "flask"})
    return containers


def calculate_average_cpu_load():
    containers = get_running_containers()
    if containers:
        total_cpu_percent = 0
        number_of_containers = 0
        for container in containers:
            try:
                container = client.containers.get(container.id)
                cpu_stats = container.stats(stream=False)

                # Calculate the CPU usage percentage
                cpu_delta = (
                    cpu_stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - cpu_stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    cpu_stats["cpu_stats"]["system_cpu_usage"]
                    - cpu_stats["precpu_stats"]["system_cpu_usage"]
                )

                num_cpus = cpu_stats["cpu_stats"]["online_cpus"]

                cpu_percent = (cpu_delta / system_delta) * 100 * num_cpus

                total_cpu_percent += cpu_percent
                number_of_containers += 1

            except Exception as err:
                print(err)

        if number_of_containers > 0:
            return round(total_cpu_percent / number_of_containers, 2)
    else:
        print("No containers running")
        return None


def start_new_container():
    server_name = f"flask{len(get_running_containers()) + 1}"
    try:
        client.containers.get(server_name)
    except docker.errors.NotFound:
        client.containers.run(
            "app1",
            cpuset_cpus="0",
            network="lb_network",
            mem_limit="200m",
            environment=[f"SERVER_NAME={server_name}"],
            hostname=server_name,
            detach=True,
            name=server_name,
        )
    else:
        print(f"Container {server_name} already exists")

        container = client.containers.get(server_name)
        container.stop()
        container.remove()

        server_name = f"flask{len(get_running_containers()) + 1}"
        client.containers.run(
            "app1",
            cpuset_cpus="0",
            network="lb_network",
            mem_limit="200m",
            environment=[f"SERVER_NAME={server_name}"],
            hostname=server_name,
            detach=True,
            name=server_name,
        )


def terminate_container():
    containers = list(reversed(get_running_containers()))
    if len(containers) > 0:
        print(f"Stopping {containers[-1].name}")

        # TODO: When server is removed from rotation, update NGINX config
        # nginx_container = client.containers.get("nginx-lb")
        container = client.containers.get(containers[-1].name)
        container.stop()
        container.remove()


def manage_containers_by_cpu_usage():
    global cooldown_time_end
    global low_cpu_count

    current_time = time.time()
    if current_time < cooldown_time_end:
        print("Cooldown active, doing nothing")
        return

    cpu_load = calculate_average_cpu_load()
    if cpu_load and cpu_load < min_cpu_load:
        low_cpu_count += 1

    if len(get_running_containers()) < min_containers:
        print("Number of containers is low, adding a new container")
        start_new_container()
        print("resetting low cpu alert")
        low_cpu_count = 0

        cooldown_time_end = current_time + 30

    elif cpu_load > target_cpu_load and len(get_running_containers()) < max_containers:
        print("CPU load is high, adding new container")
        start_new_container()
        print("resetting low cpu alert")
        low_cpu_count = 0

        cooldown_time_end = current_time + 30

    elif (
        cpu_load < target_cpu_load
        and cpu_load < min_cpu_load
        and len(get_running_containers()) > min_containers
        and current_time > cooldown_time_end + 300
        and low_cpu_count > 5
    ):
        print("CPU load has been low for more than 5mins, removing container")
        terminate_container()
        cooldown_time_end = current_time + 30
        # reload nginx container
        nginx_container = client.containers.get("nginx-lb")
        nginx_container.restart()


def main():
    while True:
        manage_containers_by_cpu_usage()
        print("Nothing to do, sleeping for 10 seconds")
        time.sleep(10)


if __name__ == "__main__":
    main()

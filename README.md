# Python Docker Autoscaling Scripts

This is a Python autoscaling tool that allows you to automatically start and stop docker containers in response to demand. The goal of this tool is to ensure that your dockerised web application can handle varying levels of traffic and load without manual intervention. 

The tool manages docker containers by monitoring their CPU load and RAM usage. When these metrics breach predefined thresholds, it starts extra containers to handle the additional load. The tool maintains a desired number of containers and will automatically stop and remove extra containers from rotation once the demand on the application goes down.

I wrote this as a proof of concept of autoscaling dockerised web applications. The code isn't perfect so use it at your own risk.


![Autoscaling screencast](autoscaling.gif)

## Contents

- `backend/` - This folder contains code to run a simple Flask application with routes to test CPU, RAM and basic connectivity.
- `nginx_config/` - This folder contains an NGINX config file to run NGINX as a load balancer for up to three docker containers running the Flask code above.
- `autoscaling.py` - The autoscaling logic that starts and stops flask containers automatically based on load.
- `locustfile.py` - Locust is a load testing tool. The code in this file simulates many HTTP requests to the web application, allowing you to test the autoscaling tool.

## Dependencies
- docker
- locust
- nginx
- python

## Setup

Follow the steps below to create an environment to test autoscaling. In the steps below, you create a docker network, build a Flask image and start an NGINX container from an image and run it using the sample configuration in this repo.

### Create a docker network
```shell
docker network create --driver=bridge --subnet=10.0.0.0/24 --ip-range=10.0.0.0/28 lb_network
```

### Build Flask Image

```shell
cd backend
docker build -t app1 .
```

### Install and run locust

Install and run Locust, a load testing tool to simulate thousands of requests to the Flask applications.

```shell
pip install locust
locust
```

Optionally, if you want to analyse the logs produced by locust, for example to test that load balancing works as expected, you can have it write logs to a file:

```shell
locust --log-file locust.log
```

## Usage

1. Start the nginx container with a custom configuration mounted as volume

Run nginx from an image and copy `nginx.conf` to it. The configuration sets nginx up as a load balancer for the Flask containers above.

```shell
docker run -p 80:80 --name nginx-lb --network=lb_network --ip 10.0.0.2 -v $(pwd)/nginx_config:/etc/nginx/conf.d nginx:latest --rm
```

2. Start the Flask container(s)

 This step is optional because the autoscaling code can automatically start flask containers for you. The best way to test this tool is to run the containers with restrictions. The example below starts two Flask containers on the same CPU on the host and limits the amount of RAM they can access.

```shell
docker run --network=lb_network --rm --ip 10.0.0.3 --name flask1  -e SERVER_NAME=flask1 --cpuset-cpus="0" --memory=200m app1
docker run --network=lb_network --rm --ip 10.0.0.4 --name flask2  -e SERVER_NAME=flask2 --cpuset-cpus="0" --memory=200m app1
```

3. Run the autoscaling script. The script will start as many containers as necessary to handle the load you will generate in the next step.

```shell
python3 autoscaling.py
```

4.  Start the Locust load tester UI and point it to the hostname the nginx container is running on. Swarm your web applications with as many requests as you like.

```shell
locust
```

5. Watch the containers scale using the `docker stats` command.

```shell
docker stats --format "table {{.Name}}\t\t {{.CPUPerc}} \t\t{{.MemUsage}}"
```


### Analyse logs from Flask containers


You can use `awk` to compare responses from each of the Flask containers like this:

```shell
awk '/flask1!$/ { count1++ } /flask2!$/ {count2++} END {print "flask1!:", count1; print "flask2!:", count2}' locust.log
```
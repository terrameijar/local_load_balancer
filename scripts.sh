# Create a docker network
docker network create --driver=bridge --subnet=10.0.0.0/24 --ip-range=10.0.0.0/28 lb_network

# Build Flask Image
docker build -t app1 .

# Run Flask containers
docker run --network=lb_network --ip 10.0.0.3 --name flask1  -e SERVER_NAME=flask1 --cpus=0.25 --rm app1
docker run --network=lb_network --ip 10.0.0.4 --name flask2  -e SERVER_NAME=flask2 --cpus=0.25 --rm app1

# Run NGINX container with custom configuration mounted as volume
docker run -p 80:80 --name nginx-lb --network=lb_network --ip 10.0.0.2 -v $(pwd)/nginx_config:/etc/nginx/conf.d nginx:latest --rm

# Install and run locust
pip install locust
locust --logfile ./locust.log 


# Analyse logs from Flask containers
awk '/flask1!$/ { count1++ } /flask2!$/ {count2++} END {print "flask1!:", count1; print "flask2!:", count2}' locust.log
from locust import HttpUser, task
import logging


class HelloWorldUser(HttpUser):
    @task
    def test_root(self):
        response = self.client.get("/")
        logging.info(f"Response: {response.content}")

    @task
    def test_fibonacci(self):
        response = self.client.get("/fibonacci")
        logging.info(f"Response: {response.content}")

    @task
    def test_memory(self):
        response = self.client.get("/memory")
        logging.info(f"Response: {response.content}")

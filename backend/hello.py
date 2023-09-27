from flask import Flask
from flask import request
import os
import random

app = Flask(__name__)


@app.route("/")
def index():
    server_name = os.environ.get("SERVER_NAME", "server 0")
    return f"Hello from {server_name}!"


def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


@app.route("/fibonacci")
def fibonacci():
    n = random.randint(1, 50)
    return str(calculate_fibonacci(n))


@app.route("/memory")
def memory():
    n = random.randint(1, 1000000)
    return str(list(range(n)))

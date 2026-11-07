import random
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

APP_NAME = "app-simon-python"
APP_PORT = 8000

app = Flask(__name__)

REQUESTS = Counter(
    "app_requests_total",           # nombre que verás en Prometheus
    "Total de peticiones HTTP",     # descripción
    ["endpoint", "status"],         # labels
)
LATENCY = Histogram(
    "app_request_duration_seconds",
    "Duración de las peticiones HTTP",
    ["endpoint"],
)


@app.get("/")
def inicio():
    return jsonify(app=APP_NAME, mensaje="Hola desde Python")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
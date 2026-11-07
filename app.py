import json                                   # --- NUEVO (paso 3)
import logging                                # --- NUEVO (paso 3)
import random
import socket                                 # --- NUEVO (paso 3)
import time
from datetime import datetime, timezone       # --- NUEVO (paso 3)

from flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

APP_NAME = "app-simon-python"
APP_PORT = 8000


# --- NUEVO (paso 3): Handler que envía cada log como UNA línea JSON por TCP a Logstash
class LogstashTcpHandler(logging.Handler):

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None          # la conexión se abre la primera vez que se necesita

    def emit(self, record):
        # 1) Armar el evento con los campos que espera Logstash/Kibana
        evento = {
            "@timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
                                  .isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,          # INFO, ERROR...
            "message": record.getMessage(),
            "application": APP_NAME,            # ¡obligatorio! nombra el índice
        }
        # 2) Convertir a JSON + salto de línea (un evento por línea)
        linea = (json.dumps(evento) + "\n").encode("utf-8")
        # 3) Enviar por TCP; si falla, reconectar una vez; si sigue fallando, no tumbar la app
        try:
            if self.sock is None:
                self.sock = socket.create_connection((self.host, self.port), timeout=2)
            self.sock.sendall(linea)
        except OSError:
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=2)
                self.sock.sendall(linea)
            except OSError:
                self.sock = None


# --- NUEVO (paso 3): logger con dos handlers (terminal + Logstash)
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)

consola = logging.StreamHandler()
consola.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(consola)
logger.addHandler(LogstashTcpHandler("localhost", 5001))


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


@app.before_request
def iniciar_cronometro():
    request.inicio = time.perf_counter()


@app.after_request
def registrar_metricas(response):
    if request.path != "/metrics":
        duracion = time.perf_counter() - request.inicio
        LATENCY.labels(request.path).observe(duracion)
        REQUESTS.labels(request.path, str(response.status_code)).inc()
    return response


@app.get("/")
def inicio():
    logger.info("Visita a la página de inicio")                                   # --- NUEVO (paso 3) INFO
    return jsonify(app=APP_NAME, mensaje="Hola desde Python")


@app.get("/procesar")
def procesar():
    espera = random.uniform(0.05, 0.8)
    time.sleep(espera)
    if espera > 0.65:
        logger.error(f"Procesamiento demasiado lento ({espera:.2f}s), se aborta")  # --- NUEVO (paso 3) ERROR
        return jsonify(error="timeout simulado"), 500
    logger.info(f"Procesamiento completado en {espera:.2f}s")                     # --- NUEVO (paso 3) INFO
    return jsonify(ok=True, segundos=round(espera, 2))


# --- NUEVO (paso 3): endpoint que siempre genera un log ERROR
@app.get("/error")
def provocar_error():
    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.error(f"Error forzado: {e}")
        return jsonify(error=str(e)), 500


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    logger.info(f"{APP_NAME} iniciando en el puerto {APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT)
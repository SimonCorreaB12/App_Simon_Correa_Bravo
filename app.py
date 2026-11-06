from flask import Flask, jsonify

APP_NAME = "app-simon-python"
APP_PORT = 8000

app = Flask(__name__)


@app.get("/")
def inicio():
    return jsonify(app=APP_NAME, mensaje="Hola desde Python")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
from flask import Flask, jsonify, request
import requests, os

app = Flask(__name__)
DOG_API = os.getenv("DOG_API_URL", "https://dog.ceo/api/breeds/image/random")

# "Base de datos" temporal en memoria
DOG_DATA = []

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

@app.route("/dog")
def get_dog():
    try:
        r = requests.get(DOG_API, timeout=5)
        data = r.json()
        return jsonify({"status": "success", "image": data.get("message")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/save", methods=["POST"])
def save_dog():
    try:
        record = request.get_json()
        if not record or "image" not in record:
            return jsonify({"error": "Invalid data"}), 400
        DOG_DATA.append(record)
        return jsonify({"status": "saved", "total": len(DOG_DATA)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/data")
def get_data():
    return jsonify({"total": len(DOG_DATA), "items": DOG_DATA})

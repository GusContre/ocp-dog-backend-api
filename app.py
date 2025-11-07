import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

DOG_API_URL = os.environ.get("DOG_API_URL", "https://dog.ceo/api/breeds/image/random")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/dog")
def dog():
    try:
        response = requests.get(DOG_API_URL, timeout=5)
        response.raise_for_status()
        payload = response.json()
        image_url = payload.get("message")

        if not image_url:
            raise ValueError("Dog API response missing 'message'")

        return jsonify({"status": "success", "image": image_url})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5002)))

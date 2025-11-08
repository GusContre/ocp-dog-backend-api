from flask import Flask, jsonify, request
import requests, os, random
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
DOG_API = os.getenv("DOG_API_URL", "https://dog.ceo/api/breeds/image/random")

# DB env vars provided by Helm (ConfigMap/Secret)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


def get_db_conn():
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS]):
        return None
    try:
        return psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=int(os.getenv("DB_PORT", 5432)),
            connect_timeout=3,
        )
    except Exception:
        return None


def ensure_schema():
    conn = get_db_conn()
    if not conn:
        return False
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dogs (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    image TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        return True
    finally:
        conn.close()

# "Base de datos" temporal en memoria
DOG_DATA = []

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

@app.route("/dog")
def get_dog():
    """Return a dog record.

    - If DB is available and has records: return one at random.
    - Else, try external API.
    - Else, return 404 guidance.
    """
    # Prefer DB if reachable
    if ensure_schema():
        conn = get_db_conn()
        if conn:
            try:
                with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT name, image FROM dogs ORDER BY random() LIMIT 1")
                    row = cur.fetchone()
                    if row and (row.get("image") or row.get("name")):
                        return jsonify({
                            "status": "success",
                            "image": row.get("image"),
                            "name": row.get("name"),
                            "source": "db",
                        })
            finally:
                conn.close()

    # No DB row found; try external API
    try:
        r = requests.get(DOG_API, timeout=5)
        r.raise_for_status()
        data = r.json()
        image = (data or {}).get("message")
        if image:
            return jsonify({"status": "success", "image": image, "source": "api"})
    except Exception:
        pass

    return jsonify({
        "status": "empty",
        "message": "No hay datos en la base. Inserta un perro con POST /save",
    }), 404

@app.route("/save", methods=["POST"])
def save_dog():
    record = request.get_json() or {}
    name = (record.get("name") or "").strip() or None
    image = (record.get("image") or "").strip() or None
    if not name and not image:
        return jsonify({"error": "Debe enviar 'name' y/o 'image'"}), 400

    if not ensure_schema():
        return jsonify({"error": "Base de datos no disponible"}), 503

    conn = get_db_conn()
    if not conn:
        return jsonify({"error": "Sin conexión a la base"}), 503

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO dogs (name, image) VALUES (%s, %s)", (name, image)
                )
        return jsonify({"status": "saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/data")
def get_data():
    if not ensure_schema():
        return jsonify({"total": 0, "items": []})
    conn = get_db_conn()
    if not conn:
        return jsonify({"total": 0, "items": []})
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, image, created_at FROM dogs ORDER BY id DESC")
            rows = cur.fetchall()
            return jsonify({"total": len(rows), "items": rows})
    finally:
        conn.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port)

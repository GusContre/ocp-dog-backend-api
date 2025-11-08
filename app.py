import os
from flask import Flask, jsonify, request

from fallback import LocalDogCatalog
from storage import DogRepository

app = Flask(__name__)

AUTO_SEED = os.getenv("DOG_AUTO_SEED", "true").lower() not in {"false", "0", "no"}

repository = DogRepository()
catalog = LocalDogCatalog()
_db_seed_checked = False


def _seed_database(conn) -> None:
    global _db_seed_checked
    if _db_seed_checked or not AUTO_SEED:
        return
    repository.seed_if_empty(conn, catalog.items)
    _db_seed_checked = True


def get_ready_connection():
    conn = repository.get_connection()
    if not conn:
        return None
    if not repository.ensure_schema(conn):
        conn.close()
        return None
    _seed_database(conn)
    return conn


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.get("/dog")
def get_dog():
    conn = get_ready_connection()
    if not conn:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Base de datos no disponible. Intenta nuevamente.",
                }
            ),
            503,
        )

    try:
        row = repository.fetch_random(conn)
        if row and (row.get("image") or row.get("name")):
            return jsonify(
                {
                    "status": "success",
                    "image": row.get("image"),
                    "name": row.get("name"),
                    "source": "db",
                }
            )
        return (
            jsonify(
                {
                    "status": "empty",
                    "message": "No hay perros en la base. Inserta uno con POST /save",
                }
            ),
            404,
        )
    finally:
        conn.close()


@app.post("/save")
def save_dog():
    record = request.get_json() or {}
    name = (record.get("name") or "").strip() or None
    image = (record.get("image") or "").strip() or None
    if not name and not image:
        return jsonify({"error": "Debe enviar 'name' y/o 'image'"}), 400

    conn = get_ready_connection()
    if not conn:
        return jsonify({"error": "Base de datos no disponible"}), 503

    try:
        repository.insert(conn, name, image)
        return jsonify({"status": "saved"})
    except Exception as exc:
        app.logger.exception("Error inserting record: %s", exc)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": str(exc)}), 500
    finally:
        conn.close()


@app.get("/data")
def get_data():
    conn = get_ready_connection()
    if conn:
        try:
            rows = repository.list_items(conn)
            return jsonify({"total": len(rows), "items": rows, "source": "db"})
        finally:
            conn.close()

    fallback_rows = catalog.enumerated()
    return jsonify({"total": len(fallback_rows), "items": fallback_rows, "source": "local"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port)

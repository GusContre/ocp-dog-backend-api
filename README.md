# ocp-dog-backend-api

Microservicio mínimo en Flask que expone dos endpoints:

- `GET /healthz` → devuelve `{ "status": "ok" }`
- `GET /dog` → consume `https://dog.ceo/api/breeds/image/random` y responde `{ "status": "success", "image": "<url>" }`

La URL del proveedor se puede sobreescribir con la variable de entorno `DOG_API_URL`. El servicio escucha en el puerto `5002`.

## Ejecución local

1. Clona este repositorio y posicionate en `ocp-dog-backend-api/`.
2. (Recomendado) Crea un entorno virtual para evitar el error de “externally-managed-environment”.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. Instala dependencias y ejecuta el servidor.

   ```bash
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Verifica que el servidor está escuchando en `http://localhost:5002`.

## Docker

1. Construye la imagen.

   ```bash
   docker build -t ocp-dog-backend-api .
   ```

2. Inicia un contenedor.

   ```bash
   docker run --rm -p 5002:5002 ocp-dog-backend-api
   ```

3. Verifica los endpoints en `http://localhost:5002/healthz` y `http://localhost:5002/dog`.

## Pruebas de la API

- **Curl o navegador**  
  ```bash
  curl http://localhost:5002/healthz     # -> {"status":"ok"}
  curl http://localhost:5002/dog         # -> {"status":"success","image":"https://..."}
  ```
  El path raíz `/` no está definido y devolverá 404; usa `/healthz` o `/dog`.

- **Postman / Alog / clientes HTTP**  
  1. Crea una petición `GET` a `http://<host>:5002/healthz` o `http://<host>:5002/dog`.  
  2. No necesitas headers ni body especiales.  
  3. Pulsa *Send* y deberías ver las respuestas JSON anteriores.  
  Si pruebas desde otra máquina, reemplaza `<host>` por la IP o hostname que expone tu equipo (ej. `192.168.x.x`) y asegúrate de tener el puerto 5002 abierto o publicado con Docker.

## CI/CD

El flujo `.github/workflows/docker-build.yml` se ejecuta en cada push a `main` y:

- Construye la imagen usando Buildx con el contexto actual del repo.
- Inicia sesión en Docker Hub usando los secretos `DOCKER_USERNAME` y `DOCKERHUB_TOKEN`.
- Publica dos tags en `docker.io/<DOCKER_USERNAME>/ocp-dog-backend-api`: `latest` y `<número_de_run>` (usa `github.run_number`), así puedes rastrear cada build.

Asegúrate de definir esos secretos en la configuración del repositorio antes de ejecutar el workflow.

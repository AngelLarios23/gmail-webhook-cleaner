from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import base64
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = FastAPI()

# Ruta absoluta a la carpeta frontend (un nivel arriba de backend)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Servir archivos estáticos desde la carpeta frontend
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    print(f"⚠️ Carpeta frontend no encontrada en {frontend_path}")

# Lista temporal para almacenar correos
emails = []

# Clasificador de spam básico (ejemplo simple)
def es_spam(subject: str) -> bool:
    spam_keywords = ["dinero", "oferta", "gratis", "premio", "ganar"]
    return any(word.lower() in subject.lower() for word in spam_keywords)

# Extraer cuerpo de un mensaje (texto plano o HTML)
def extract_body(msg):
    body_text = ""
    payload = msg.get("payload", {})

    # Caso 1: cuerpo directo
    if "data" in payload.get("body", {}):
        body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    # Caso 2: partes (texto plano o html)
    elif "parts" in payload:
        for part in payload["parts"]:
            if "data" in part.get("body", {}):
                body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break

    return body_text

# Cargar credenciales desde token.json (ruta segura)
def get_gmail_service():
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    creds = Credentials.from_authorized_user_file(
        token_path, ["https://www.googleapis.com/auth/gmail.readonly"]
    )
    return build("gmail", "v1", credentials=creds)

@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    body = await request.json()
    message = body.get("message", {})
    data = message.get("data")

    if not data:
        return {"status": "no data"}

    # Decodificar el mensaje de Pub/Sub
    decoded = base64.b64decode(data).decode("utf-8")
    print(f"📩 Mensaje recibido: {decoded}")

    # Extraer historyId de forma robusta
    history_id = None
    try:
        payload = json.loads(decoded)
        history_id = int(payload.get("historyId"))
    except Exception as e:
        print(f"⚠️ Error al extraer historyId: {e}")

    if history_id:
        try:
            service = get_gmail_service()
            history = service.users().history().list(userId="me", startHistoryId=history_id).execute()
            if "history" in history:
                for h in history["history"]:
                    if "messagesAdded" in h:
                        for m in h["messagesAdded"]:
                            msg_id = m["message"]["id"]
                            msg = service.users().messages().get(
                                userId="me",
                                id=msg_id,
                                format="full",
                                metadataHeaders=["From", "Subject"]
                            ).execute()
                            headers = msg.get("payload", {}).get("headers", [])
                            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(sin asunto)")
                            sender = next((h["value"] for h in headers if h["name"] == "From"), "(sin remitente)")
                            body_text = extract_body(msg)

                            spam_flag = es_spam(subject)

                            emails.append({
                                "id": len(emails) + 1,
                                "from": sender,
                                "subject": subject,
                                "is_spam": spam_flag,
                                "body": body_text,
                                "date": int(msg.get("internalDate", 0))
                            })

                            print(f"✅ Nuevo correo de {sender} con asunto: {subject} | {'🚫 SPAM' if spam_flag else '✅ Legítimo'}")
        except Exception as e:
            print(f"⚠️ Error al consultar Gmail: {e}")

    return {"status": "ok"}

@app.get("/emails")
async def get_emails():
    sorted_emails = sorted(emails, key=lambda e: e.get("date", 0), reverse=True)
    return JSONResponse(content=[
        {"id": e["id"], "from": e["from"], "subject": e["subject"], "is_spam": e["is_spam"]}
        for e in sorted_emails
    ])

@app.get("/emails/{email_id}")
async def get_email(email_id: int):
    for e in emails:
        if e["id"] == email_id:
            return JSONResponse(content=e)
    return {"error": "Correo no encontrado"}

@app.post("/test-email")
async def test_email():
    emails.append({
        "id": len(emails) + 1,
        "from": "prueba@correo.com",
        "subject": "¡Has ganado un premio!",
        "is_spam": True,
        "body": "Este es un correo simulado para probar la interfaz.",
        "date": int(os.path.getmtime(__file__))  # usa timestamp actual como fecha
    })
    print("🧪 Correo simulado agregado")
    return {"status": "correo simulado agregado"}

@app.post("/activate-watch")
async def activate_watch():
    try:
        # Cargar credenciales
        token_path = os.path.join(os.path.dirname(__file__), "token.json")
        creds = Credentials.from_authorized_user_file(token_path, ["https://www.googleapis.com/auth/gmail.readonly"])
        service = build("gmail", "v1", credentials=creds)

        # Obtener el historyId actual
        profile = service.users().getProfile(userId="me").execute()
        start_history_id = profile.get("historyId")

        # Activar el watch
        request_body = {
            "topicName": "projects/prueba-478901/topics/gmail-notify",
            "labelIds": ["INBOX"],
            "labelFilterAction": "include",
            "startHistoryId": start_history_id
        }

        resp = service.users().watch(userId="me", body=request_body).execute()

        print("✅ Watch activado")
        print("📌 Expira en:", resp.get("expiration"))
        print("📩 historyId inicial:", resp.get("historyId"))

        return {
            "status": "watch activado",
            "expiration": resp.get("expiration"),
            "historyId": resp.get("historyId")
        }

    except Exception as e:
        print(f"⚠️ Error al activar el watch: {e}")
        return {"error": str(e)}

# Nuevo endpoint: cargar todos los correos de la bandeja
@app.post("/load-all-emails")
async def load_all_emails():
    try:
        service = get_gmail_service()
        response = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=20).execute()
        message_ids = [msg["id"] for msg in response.get("messages", [])]

        for msg_id in message_ids:
            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full",
                metadataHeaders=["From", "Subject"]
            ).execute()
            headers = msg.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(sin asunto)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "(sin remitente)")
            body_text = extract_body(msg)

            spam_flag = es_spam(subject)

            emails.append({
                "id": len(emails) + 1,
                "from": sender,
                "subject": subject,
                "is_spam": spam_flag,
                "body": body_text,
                "date": int(msg.get("internalDate", 0))
            })

        print(f"📥 Se cargaron {len(message_ids)} correos desde Gmail")
        return {"status": "correos cargados", "total": len(message_ids)}

    except Exception as e:
        print(f"⚠️ Error al cargar correos: {e}")
        return {"error": str(e)}
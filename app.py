from fastapi import FastAPI, Request
import base64, json

app = FastAPI()

@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    envelope = await request.json()
    message = envelope.get("message", {})
    data_b64 = message.get("data")
    if data_b64:
        decoded = base64.b64decode(data_b64).decode("utf-8")
        payload = json.loads(decoded)
        print("📩 Mensaje recibido:", payload)
    return {"status": "ok"}
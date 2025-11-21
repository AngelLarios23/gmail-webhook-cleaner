from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Alcance mínimo para leer correos
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Cargar credenciales desde token.json
creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# Construir cliente de Gmail API
gmail = build('gmail', 'v1', credentials=creds)

# Configurar el watch
request_body = {
    "topicName": "projects/prueba-478901/topics/gmail-notify",  # tu tópico Pub/Sub
    "labelIds": ["INBOX"]  # opcional: solo notifica correos nuevos en la bandeja de entrada
}

resp = gmail.users().watch(userId='me', body=request_body).execute()

print("✅ Watch activado")
print("📌 Expira en:", resp.get("expiration"))
print("📩 historyId inicial:", resp.get("historyId"))
# SpamCleaner

Aplicación que recibe notificaciones de Gmail vía Pub/Sub en un **webhook FastAPI**, clasifica los correos como 🚫 SPAM o ✅ legítimos, y los muestra en una página web con frontend sencillo.

---

## 📁 Estructura del proyecto
SpamCleaner/ ├── backend/ │   ├── app.py              # Webhook FastAPI + endpoints │   ├── activate_watch.py   # Script para activar Gmail watch │   ├── auth_bootstrap.py   # Script para autenticación inicial │   ├── token.json          # Token de acceso Gmail API │   ├── credentials.json    # Credenciales OAuth │   └── .gitignore          # Ignora credenciales y cachés ├── frontend/ │   ├── index.html          # Página principal │   ├── styles.css          # Estilos │   └── script.js           # Lógica para consumir API


---

## 🚀 Cómo iniciar el backend

1. Instala dependencias:
   ```bash
   pip install fastapi uvicorn google-api-python-client google-auth

2. Desde la raíz del proyecto, inicia el servidor:
uvicorn backend.app:app --reload
3. Abre en tu navegador:
http://localhost:8000

## SEGURIDAD

# token.json
# credentials.json
# __pycache__/
# .env (AUN NO LO USO)
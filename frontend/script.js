async function loadEmails() {
  const res = await fetch("/emails");
  const data = await res.json();
  const container = document.getElementById("emails");
  container.innerHTML = "";

  data.forEach(email => {
    const div = document.createElement("div");
    div.className = "email" + (email.is_spam ? " spam" : "");
    div.onclick = () => showEmail(email.id);

    div.innerHTML = `
      <div class="subject">${email.subject}</div>
      <div class="from">De: ${email.from}</div>
      <div class="tag">${email.is_spam ? "🚫 SPAM" : "✅ Legítimo"}</div>
    `;

    container.appendChild(div);
  });
}

async function showEmail(id) {
  const res = await fetch(`/emails/${id}`);
  const email = await res.json();
  const detail = document.getElementById("detail");
  detail.classList.remove("hidden");

  detail.innerHTML = `
    <h2>${email.subject}</h2>
    <p><strong>De:</strong> ${email.from}</p>
    <p><strong>Estado:</strong> ${email.is_spam ? "🚫 SPAM" : "✅ Legítimo"}</p>
    <hr>
    <p>${email.body || "(sin contenido)"}</p>
  `;
}
function activarWatch() {
  fetch("/activate-watch", { method: "POST" })
    .then(res => res.json())
    .then(data => {
      console.log("🔔 Watch activado:", data);
      alert("Watch activado desde historyId " + data.historyId);
    })
    .catch(err => {
      console.error("❌ Error al activar el watch:", err);
      alert("Error al activar el watch");
    });
}
function loadAllEmails() {
  fetch("/load-all-emails", { method: "POST" })
    .then(res => res.json())
    .then(data => {
      console.log("📥 Correos cargados:", data);
      // Después de cargar, refrescamos la lista
      loadEmails();
      alert("Se cargaron " + data.total + " correos desde Gmail");
    })
    .catch(err => {
      console.error("❌ Error al cargar correos:", err);
      alert("Error al cargar correos");
    });
}
setInterval(loadEmails, 3000);
loadEmails();
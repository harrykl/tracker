import os
import requests

# GitHub Token aus Umgebungsvariable lesen
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Prüfen, ob der Token vorhanden ist
if not GITHUB_TOKEN:
    print("❌ Kein GitHub Token gefunden. Bitte GITHUB_TOKEN als Umgebungsvariable setzen.")
else:
    # Anfrage an die GitHub API senden
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get("https://api.github.com/user", headers=headers)

    # Antwort ausgeben
    print(f"Statuscode: {response.status_code}")
    print("Antwort:")
    print(response.json())

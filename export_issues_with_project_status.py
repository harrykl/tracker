import os
import csv
import requests
import sys

# GitHub GraphQL API Endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# 🔧 Trage hier deine Repository-Informationen ein
REPO_OWNER = "harrykl"
REPO_NAME = "tracker"

# 🔐 GitHub Token aus Umgebungsvariable lesen
GITHUB_TOKEN = os.getenv("GH_TOKEN")

if not GITHUB_TOKEN:
    print("❌ Fehler: GITHUB_TOKEN ist nicht gesetzt.")
    sys.exit(1)

# GraphQL-Abfrage mit korrekter Behandlung von Union-Typen
query = f"""

query {
  repository(owner = REPO_OWNER, name = REPO_NAME) {
    issues(first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        updatedAt
        projectItems(first: 5) {
          nodes {
            fieldValues(first: 10) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue {
                  field {
                    name
                  }
                  name
                }
                ... on ProjectV2ItemFieldTextValue {
                  field {
                    name
                  }
                  text
                }
                ... on ProjectV2ItemFieldDateValue {
                  field {
                    name
                  }
                  date
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

# Anfrage senden
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)
data = response.json()

# Fehlerbehandlung
if "errors" in data:
    print("❌ Fehlerhafte API-Antwort:", data["errors"])
    sys.exit(1)

if "data" not in data:
    print("❌ Fehler: API-Antwort enthält keinen 'data'-Schlüssel.")
    sys.exit(1)

# Daten extrahieren
issues = data["data"]["repository"]["issues"]["nodes"]

# CSV schreiben
os.makedirs("Prozessmetriken", exist_ok=True)
with open("Prozessmetriken/issue_project_status.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Issue-ID", "Title", "Status", "Projektstatus", "Zeitstempel"])
    for issue in issues:
        project_status = ""
        for item in issue.get("projectItems", {}).get("nodes", []):
            for field in item.get("fieldValues", {}).get("nodes", []):
                if field.get("field", {}).get("name") == "Status":
                    project_status = field.get("name") or field.get("text") or field.get("date") or ""
        writer.writerow([
            issue["number"],
            issue["title"],
            issue["state"],
            project_status,
            issue["updatedAt"]
        ])

print("✅ CSV-Datei erfolgreich erstellt: Prozessmetriken/issue_project_status.csv")

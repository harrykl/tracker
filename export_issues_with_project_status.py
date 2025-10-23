import os
import csv
import requests
import sys
from datetime import datetime

# GitHub GraphQL API Endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# 🔧 Repository-Informationen
REPO_OWNER = "harrykl"
REPO_NAME = "tracker"

# 🔐 GitHub Token aus Umgebungsvariable lesen
GITHUB_TOKEN = os.getenv("GH_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Fehler: GITHUB_TOKEN ist nicht gesetzt.")
    sys.exit(1)

# GraphQL-Abfrage mit korrekter Behandlung von Union-Typen
query = """
query {
  repository(owner: "harrykl", name: "tracker") {
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
                  field { ... on ProjectV2FieldCommon { name } }
                  name
                }
                ... on ProjectV2ItemFieldTextValue {
                  field { ... on ProjectV2FieldCommon { name } }
                  text
                }
                ... on ProjectV2ItemFieldDateValue {
                  field { ... on ProjectV2FieldCommon { name } }
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

issues = data["data"]["repository"]["issues"]["nodes"]

# CSV vorbereiten
os.makedirs("Prozessmetriken", exist_ok=True)
csv_path = "Prozessmetriken/issue_project_status.csv"

# Vorhandene Daten laden, um Duplikate zu vermeiden
existing_rows = set()
if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["Issue-ID"], row["Projektstatus"])
            existing_rows.add(key)

# Neue Daten ergänzen
with open(csv_path, mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Header nur schreiben, wenn Datei neu
    if os.path.getsize(csv_path) == 0:
        writer.writerow(["Issue-ID", "Title", "Status", "Projektstatus", "Zeitstempel"])

    for issue in issues:
        issue_number = issue["number"]
        issue_title = issue["title"]
        issue_state = issue["state"]
        updated_at = issue["updatedAt"]

        project_status = ""
        for item in issue.get("projectItems", {}).get("nodes", []):
            for field in item.get("fieldValues", {}).get("nodes", []):
                field_name = field.get("field", {}).get("name")
                if field_name == "Status":
                    project_status = field.get("name") or field.get("text") or field.get("date") or ""

        if not project_status:
            continue  # Kein Status-Feld gefunden

        key = (str(issue_number), project_status)
        if key not in existing_rows:
            writer.writerow([
                issue_number,
                issue_title,
                issue_state,
                project_status,
                updated_at
            ])
            existing_rows.add(key)

print("✅ CSV-Datei erfolgreich aktualisiert:", csv_path)

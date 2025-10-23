import os
import csv
import requests
import sys

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

# Bestehende Tabelle laden
table = {}
all_statuses = set()
if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            issue_id = row["Issue-ID"]
            table[issue_id] = row
            all_statuses.update(row.keys())

# Neue Daten einlesen
for issue in issues:
    issue_id = str(issue["number"])
    title = issue["title"]
    updated_at = issue["updatedAt"]
    state = issue["state"]

    # Status-Feld aus Project Items holen
    project_status = None
    for item in issue.get("projectItems", {}).get("nodes", []):
        for field in item.get("fieldValues", {}).get("nodes", []):
            if field.get("field", {}).get("name") == "Status":
                project_status = field.get("name") or field.get("text") or field.get("date")

    if not project_status:
        continue

    all_statuses.add(project_status)

    # Falls Issue noch nicht existiert → neue Zeile anlegen
    if issue_id not in table:
        table[issue_id] = {
            "Issue-ID": issue_id,
            "Title": title,
            "GitHub-State": state,
            "Last-UpdatedAt": updated_at
        }

    row = table[issue_id]

    # Immer aktualisieren, falls sich der GitHub-State oder updatedAt geändert hat
    row["GitHub-State"] = state
    row["Last-UpdatedAt"] = updated_at

    # Wenn dieser Status noch keinen Zeitstempel hat → hinzufügen
    if not row.get(project_status):
        row[project_status] = updated_at

# CSV neu schreiben (alle Issues, alle bekannten Status-Spalten)
# „Issue-ID“, „Title“, „GitHub-State“ und „Last-UpdatedAt“ stehen immer am Anfang
fixed_columns = ["Issue-ID", "Title", "GitHub-State", "Last-UpdatedAt"]
status_columns = sorted(s for s in all_statuses if s not in fixed_columns)
all_columns = fixed_columns + status_columns

with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=all_columns)
    writer.writeheader()
    for row in table.values():
        writer.writerow(row)

print("✅ CSV-Datei erfolgreich erstellt/aktualisiert:", csv_path)

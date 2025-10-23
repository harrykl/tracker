import os
import csv
import requests

# GitHub GraphQL API Endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# GitHub Token und Repository-Informationen
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "dein-benutzername"
REPO_NAME = "dein-repo-name"

# GraphQL-Abfrage
query = f"""
query {{
  repository(owner: "{REPO_OWNER}", name: "{REPO_NAME}") {{
    issues(first: 50, orderBy: {{field: UPDATED_AT, direction: DESC}}) {{
      nodes {{
        number
        title
        state
        updatedAt
        projectItems(first: 5) {{
          nodes {{
            fieldValues(first: 10) {{
              nodes {{
                field {{
                  name
                }}
                ... on ProjectV2ItemFieldSingleSelectValue {{
                  name
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

# Anfrage senden
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)
data = response.json()

# CSV-Datei schreiben
issues = data["data"]["repository"]["issues"]["nodes"]
with open("Prozessmetriken/issue_project_status.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Issue-ID", "Title", "Status", "Projektstatus", "Zeitstempel"])
    for issue in issues:
        project_status = ""
        for item in issue["projectItems"]["nodes"]:
            for field in item["fieldValues"]["nodes"]:
                if field["field"]["name"] == "Status":
                    project_status = field.get("name", "")
        writer.writerow([
            issue["number"],
            issue["title"],
            issue["state"],
            project_status,
            issue["updatedAt"]
        ])

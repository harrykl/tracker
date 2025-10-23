import os
import csv
import requests

# GitHub GraphQL API Endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# GitHub Token and Repository Information
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER, REPO_NAME = os.getenv("GITHUB_REPOSITORY").split("/")

# GraphQL Query with correct handling of union types
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
                ... on ProjectV2ItemFieldTextValue {{
                  text
                }}
                ... on ProjectV2ItemFieldDateValue {{
                  date
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

# Send request to GitHub GraphQL API
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)
data = response.json()

# Check for errors in the response
if "errors" in data:
    print("Fehlerhafte API-Antwort:", data["errors"])
    exit(1)

# Extract issue data
issues = data["data"]["repository"]["issues"]["nodes"]

# Write to CSV file
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

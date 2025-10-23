import csv
import os
from datetime import datetime
from github import Github

# GitHub token and repository details
token = os.getenv('GITHUB_TOKEN')
repo_name = os.getenv('GITHUB_REPOSITORY')

# Authenticate with GitHub
g = Github(token)
repo = g.get_repo(repo_name)

# Create directory for metrics if it doesn't exist
metrics_dir = "Prozessmetriken"
os.makedirs(metrics_dir, exist_ok=True)

# Prepare CSV file path
csv_file_path = os.path.join(metrics_dir, "issue_status_metrics.csv")

# Fetch all issues from the repository
issues = repo.get_issues(state='all')

# Write issue data to CSV
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Issue-ID", "Title", "Status", "Zeitstempel"])
    for issue in issues:
        writer.writerow([issue.number, issue.title, issue.state, issue.updated_at.strftime("%Y-%m-%d %H:%M:%S")])

print(f"Issue status metrics saved to {csv_file_path}")

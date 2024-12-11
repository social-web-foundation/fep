from datetime import timedelta, date
from urllib.request import Request, urlopen

import json

from .fep_file import FepFile

DRAFT_FEP_LABEL = 149758


def create_body(filename: str, date_received: date):
    date1 = date_received.isoformat()
    date2 = (date_received + timedelta(days=365)).isoformat()

    body = f"""
The [proposal](https://codeberg.org/fediverse/fep/src/branch/main/{filename}) has been received. Thank you!

This issue tracks discussions and updates to the proposal during the `DRAFT` period.

Please post links to relevant discussions as comment to this issue.

`dateReceived`: {date1}

If no further actions are taken, the proposal may be set by the facilitators to `WITHDRAWN` on {date2} (in 1 year).
    """

    return body

def create_codeberg_issue(owner, repo, token, title, body):
    request = Request(
    f"https://codeberg.org/api/v1/repos/{owner}/{repo}/issues"
)
    request.add_header("Content-Type", "application/json; charset=utf-8")
    request_body = json.dumps(
        {"title": title, "body": body, "labels": [DRAFT_FEP_LABEL]}
    ).encode("utf-8")
    request.add_header("authorization", f"Bearer {token}")
    request.add_header("Content-Length", len(request_body))
    request.data = request_body
    response = urlopen(request)

    issue_url = json.loads(response.read())["html_url"]

    return issue_url

def create_issue(owner, repo, token, slug):

    fep_file = FepFile(slug)

    if "trackingIssue" in fep_file.parsed_frontmatter:
        print("File already has trackingIssue")
        exit(1)

    title = f"[TRACKING] FEP-{slug}: {fep_file.title}"

    date_received = date.fromisoformat(fep_file.parsed_frontmatter["dateReceived"])

    body = create_body(fep_file.filename, date_received)

    issue_url = create_codeberg_issue(owner, repo, token, title, body)

    fep_file.frontmatter.append(f"trackingIssue: {issue_url}")
    if "discussionsTo" not in fep_file.parsed_frontmatter:
        fep_file.frontmatter.append(f"discussionsTo: {issue_url}")
    fep_file.write()

    print(f"Issue url: {issue_url} for {title}")

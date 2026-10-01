import requests
import time

GITHUB_TOKEN = "~[GITHUB_PERSONAL_TOKEN_0]~"
SLACK_WEBHOOK = "~[SLACK_WEBHOOK_URL_0]~"
PAGERDUTY_KEY = "~[PAGERDUTY_KEY_0]~"
REPOS = ["myorg/api-service", "myorg/frontend", "myorg/data-pipeline"]

def get_open_prs(repo):
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/pulls",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        params={"state": "open"}
    )
    return resp.json()

def get_failing_checks(repo, sha):
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs",
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    runs = resp.json().get("check_runs", [])
    return [r for r in runs if r["conclusion"] == "failure"]

def notify_slack(message, channel="#dev-alerts"):
    requests.post(SLACK_WEBHOOK, json={"text": message, "channel": channel})

def page_oncall(message):
    requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json={"routing_key": PAGERDUTY_KEY, "event_action": "trigger",
              "payload": {"summary": message, "severity": "critical", "source": "github-monitor"}}
    )

def run_monitor():
    while True:
        for repo in REPOS:
            prs = get_open_prs(repo)
            for pr in prs:
                failures = get_failing_checks(repo, pr["head"]["sha"])
                if failures:
                    msg = f"❌ {len(failures)} check(s) failing on PR #{pr['number']} in {repo}: {pr['title']}"
                    notify_slack(msg)
                    if len(failures) > 3:
                        page_oncall(msg)
        time.sleep(300)

if __name__ == "__main__":
    run_monitor()

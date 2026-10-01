import psycopg2
import sendgrid
from sendgrid.helpers.mail import Mail

DB_URL = "~[DATABASE_URL_0]~"
SENDGRID_KEY = "~[SENDGRID_API_KEY_0]~"
REPORT_FROM = "~[EMAIL_1]~"
REPORT_TO = ["~[EMAIL_2]~", "~[EMAIL_0]~"]

def get_pr_stats(days=7):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT repo, COUNT(*) as prs, AVG(merge_time_hours) as avg_merge_hours
        FROM pull_requests
        WHERE created_at > NOW() - INTERVAL '%s days'
        GROUP BY repo ORDER BY prs DESC
    """, (days,))
    return cur.fetchall()

def send_weekly_report():
    stats = get_pr_stats()
    rows = "\n".join(f"  {repo}: {prs} PRs, avg {round(hrs,1)}h to merge"
                     for repo, prs, hrs in stats)
    body = f"Weekly PR Report\n\n{rows}"
    sg = sendgrid.SendGridAPIClient(SENDGRID_KEY)
    for to in REPORT_TO:
        msg = Mail(from_email=REPORT_FROM, to_emails=to,
                   subject="Weekly PR Stats", plain_text_content=body)
        sg.send(msg)

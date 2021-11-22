import os, sys, requests
import xml.etree.ElementTree as ET
from github import Github

######## GITHUB ########
# Initialize Github
def init_github():
    global github_repo
    # Get Github token and repo slug from environment variables
    token = os.getenv('GITHUB_TOKEN')
    github_repo_slug = os.getenv('GITHUB_REPO_SLUG')

    # Create github object
    github = Github(token)
    # Create github repo object
    github_repo = github.get_repo(github_repo_slug)

# PR comment posting
def github_pr_comment_post(pr_id, pr_comment):
    init_github()
    # Create github issue object from repo
    issue = github_repo.get_issue(int(pr_id))
    # Create a comment in the Github issue
    issue.create_comment(pr_comment)
    print("Posted to Github PR.")
    return

# Posting Jacoco report summary as a PR Comment
def github_pr_comment_jacoco_sum_post(pr_id, jacoco_xml_path):
    total_covered = 0
    total_missed = 0

    # Fetch jacoco summary dictionary from the jacoco xml report
    jacoco_summary = jacoco_xml_summary_parse(jacoco_xml_path)
    pr_comment = "Test Coverage Summary: <br>"
    # Iterate through coverage types
    for coverage_type in jacoco_summary.keys():
        # Fetch values and update totals
        covered = int(jacoco_summary[coverage_type]["covered"])
        total_covered += covered
        missed = int(jacoco_summary[coverage_type]["missed"])
        total_missed += missed
        coverage = float((covered) / (covered + missed) * 100)

        pr_comment += "- {0} (coverage {1:.2f}%): covered - {2} | missed - {3} <br>".format(
            coverage_type,
            coverage,
            covered,
            missed
        )
    # Calculate total coverage
    total_coverage = float((total_covered) / (total_covered + total_missed) * 100)
    pr_comment += "{0} (coverage {1:.2f}%): covered - {2} | missed - {3}".format(
        "Total",
        total_coverage,
        total_covered,
        total_missed
    )
    # Post PR comment to github
    github_pr_comment_post(pr_id=pr_id, pr_comment=pr_comment)

######## SLACK ########
# Initialize Slack
def init_slack():
    global slack_webhook_url
    # Get Slack webhook url from enviroment variables
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')


def slack_msg_post(slack_message):
    init_slack()
    payload = '{"text":"%s"}' % slack_message
    # Post data to Slack channel
    response = requests.post(slack_webhook_url, data=payload)
    print("Posted to Slack.")
    print(response.text)
    return

######## JACOCO ########
# Parse Jacoco XML report
def jacoco_xml_summary_parse(reportPath):
    # Parse xml
    tree = ET.parse(reportPath)
    root = tree.getroot()
    summary = {}
    # Iterate through top level 'counter' nodes
    for child in root.findall("./counter"):
        # Add to summary dictionary
        summary[child.attrib["type"]] = {
            "missed": child.attrib["missed"], "covered": child.attrib["covered"]}
    
    return summary

######## main ########
def main():
    script = sys.argv[0]
    resource = sys.argv[1]
    action = sys.argv[2]
    payload = sys.argv[3:]

    if resource == "github-pr-comment":
        if action == "post":
            github_pr_comment_post(pr_id=payload[0], pr_comment=payload[1])

    if resource == "github-pr-comment-jacoco-summary":
        if action == "post":
            github_pr_comment_jacoco_sum_post(pr_id=payload[0], jacoco_xml_path=payload[1])

    if resource == "slack-msg":
        if action == "post":
            slack_msg_post(slack_message=payload[0])


if __name__ == "__main__":
    main()

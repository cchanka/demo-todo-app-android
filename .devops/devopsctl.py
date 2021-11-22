import os, sys, requests
from github import Github

######## GITHUB ########
# Initialize Github
def init_github():
    global github_repo
    # Get Github token and repo slug from environment variables
    token = os.getenv('GITHUB_TOKEN')
    github_repo_slug = os.getenv('GITHUB_REPO_SLUG')
    print(token)
    print(github_repo_slug)
    # Create github object
    github = Github(token)
    # Create github repo object
    github_repo = github.get_repo(github_repo_slug)

# PR comment posting
def github_pr_comment_post(payload):
    init_github()
    # Create github issue object from repo
    issue = github_repo.get_issue(int(payload[0]))
    # Create a comment in the Github issue
    issue.create_comment(payload[1])
    print("PR comment updated.")
    return

######## SLACK ########
# Initialize Slack
def init_slack():
    global slack_webhook_url
    # Get Slack webhook url from enviroment variables
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

def slack_msg_post(payload):
    init_slack()
    payload = '{"text":"%s"}' % payload[0]
    # Post data to Slack channel
    response = requests.post(slack_webhook_url, data=payload)
    print("Posted to Slack.")
    print(response.text)
    return

######## main ########
def main():
    script = sys.argv[0]
    resource = sys.argv[1]
    action = sys.argv[2]
    payload = sys.argv[3:]

    if resource == "github-pr-comment":
        if action == "post":
            github_pr_comment_post(payload)

    if resource == "slack-msg":
        if action == "post":
            slack_msg_post(payload)
  
if __name__ == "__main__":
    main()
import os, sys
from github import Github

token = os.getenv('GITHUB_TOKEN')
print(token)
github = Github(token)
github_repo_slug = os.getenv('GITHUB_REPO_SLUG')
print(github_repo_slug)
repo = github.get_repo(github_repo_slug)
    

def pr_comment_update(payload):
    issue = repo.get_issue(int(payload[0]))
    issue.create_comment(payload[1])
    print("PR comment updated.")
    return
      
def main():
    script = sys.argv[0]
    resource = sys.argv[1]
    action = sys.argv[2]
    payload = sys.argv[3:]

    if resource == "pr-comment":
        if action == "update":
            pr_comment_update(payload)
  
if __name__ == "__main__":
    main()
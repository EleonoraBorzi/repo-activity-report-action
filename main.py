import requests
import json 
from github import Github
import sys 
import os

headers = {"Accept": "application/vnd.github.v3+json"}

def write_comment(git_token, repo_name, issue_number, report):
    g = Github(git_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(issue_number)
    pr.create_issue_comment(report)

def reviewed_pr(url):
    url = url + "/pulls"
    payload = requests.get(url=url, headers=headers).json()
    #print(payload)

def reviewed_issues(url):
    print()

def list_reviwed_issues(url):
    print()

def list_reviwed_pr(url):
    print()

def average_pr_close_time(url):
    print()

def average_issue_close_time(url):
    print()

def average_pr_response_time(url):
    print()

def average_issue_response_time(url):
    print()

def lizard():
    stream = os.popen("lizard")
    output = stream.read()
    print("lizard:\n")
    print(output)

def main():
    #repo_name = sys.argv[1]
    #issue_number = sys.argv[2]
    #git_token = sys.argv[3]
    #url = "https://api.github.com/repo/" + str(repo_name)

    #dummy input
    repo_name = "jhy/jsoup"
    url = "https://api.github.com/repos/" + str(repo_name)

    reviewed_pr(url)
    reviewed_issues(url)
    list_reviwed_issues(url)
    list_reviwed_pr(url)
    average_pr_close_time(url)
    average_issue_close_time(url)
    average_pr_response_time(url)
    average_issue_response_time(url)
    lizard()

    report = "Report"
    #write_comment(git_token, repo_name, issue_number, report)
    print(report)

if __name__ == "__main__":
    main()





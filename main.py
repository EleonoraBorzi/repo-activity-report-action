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

def lizard(include_warnings=False):
    stream = os.popen("lizard")
    output = stream.read()
    search_string = "Total nloc"
    if include_warnings:
        # Could also combine them by utilizing that '(cyclomatic_complexity > 15 or length > 1000 or nloc > 1000000 or parameter_count > 100)'
        # appears in both cases. However then you need to do some extra work to include the beginning of the line, since we can't just continue from where this
        # substring is found.
        alternative_string1 = "!!!! Warnings"
        alternative_string2 = "No thresholds exceeded"
        if alternative_string1 in output:
            search_string = alternative_string1
        elif alternative_string2 in output:
            search_string = alternative_string2
    return output[output.index(search_string) : ]
    

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





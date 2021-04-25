import requests
import json 
from github import Github
import sys 
import os
import datetime

headers = {"Accept": "application/vnd.github.v3+json"}

def get_contributors(url):
    url = url + "/contributors"
    page_num = 1
    per_page = 100
    max_non_anonymous_users = 500
    params = {"state":"all", "per_page":per_page, "page":page_num, "anon":0}
    print(requests.get(url=url, headers=headers, params=params))
    payload = requests.get(url=url, headers=headers, params=params).json()
    contributors = []
    while len(payload) > 0:
        for user in payload:
            if len(contributors) >= max_non_anonymous_users:
                break
            contributors.append(user["login"])
        if len(contributors) >= max_non_anonymous_users:
                break
        page_num += 1
        params = {"state":"all", "per_page":"100", "page":page_num}
        payload = requests.get(url=url, headers=headers, params=params).json()
    return contributors

# Returns a bool indicating if there was at least one comment from a contributor. If true, then a timestamp of the comment is returned as well.
# If false then the second value is None.
# The returned timestamp is of the earliest eligible comment. 
def get_first_contributor_issue_comment(item : "json object of issue", contributors : "list of str") -> "bool, datetime | None":
    contributor_comment = False
    comment_timestamp = None
    page_num_comments = 1
    params_comments = {"per_page":"100", "page":page_num_comments}
    payload_comments = requests.get(url=item["comments_url"], headers=headers, params=params_comments).json()
    
    # "Issue Comments are ordered by ascending ID."
    # I believe this means that we are given the older ones first?
    while len(payload_comments) > 0:
        for comment in payload_comments:
            if comment["user"]["login"] in contributors:
                contributor_comment = True
                comment_timestamp = datetime.datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                break
        if contributor_comment:
            break
        page_num_comments += 1
        params_comments = {"per_page":"100", "page":page_num_comments}
        payload_comments = requests.get(url=it["comments_url"], headers=headers, params=params_comments).json()
    
    return contributor_comment, comment_timestamp

def get_non_contributor_issues_and_pr(url, contributors):
    url = url + "/issues"
    page_num = 1
    params = {"state":"all", "per_page":"100", "page":page_num}
    payload = requests.get(url=url, headers=headers, params=params).json()
    issues = []
    pull_requests = []
    while len(payload) > 0:
        for item in payload:
            if item["user"]["login"] in contributors:
                continue
            if "pull_request" in item:
                # 'issues' return both issues and pull requests
                pull_requests.append(item)
            else:
                issues.append(item)
        page_num += 1
        params = {"state":"all", "per_page":"100", "page":page_num}
        payload = requests.get(url=url, headers=headers, params=params).json()
    
    return issues, pull_requests

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

def average_pr_response_time(url, contributors):
    # Need issues comments, review comments and commit comments 
    print()

def average_issue_response_time(url, issues, contributors):
    responded_durations = []
    not_responded_durations = []
    
    for issue in issues:
        print("Author association: ", issue["author_association"])
        issue_created_date = datetime.datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if issue["comments"] == 0:
            today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
            not_responded_durations.append((today_formatted - issue_created_date).total_seconds())
        else:
            contributor_comment, comment_timestamp = get_first_contributor_issue_comment(issue, contributors)
            if contributor_comment:
                responded_durations.append((comment_timestamp - issue_created_date).total_seconds())
            else:
                today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
                not_responded_durations.append((today_formatted - issue_created_date).total_seconds())
        print(issue["url"], issue["comments"])


    average_responded_time = float(sum(responded_durations)) / (len(responded_durations))
    average_not_responded_time = float(sum(not_responded_durations)) / (len(not_responded_durations))
    print("Average time until issue is commented on by contributor: ", average_responded_time)
    print("Average time opened for issues without contributor comments: ", average_not_responded_time)



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
    repo_name = "KTH/devops-course" # "SoffanG17/SoffanG17" #"EleonoraBorzis/group-validity-action" #"jhy/jsoup"
    url = "https://api.github.com/repos/" + str(repo_name)
    contributors = get_contributors(url)


    #reviewed_pr(url)
    #reviewed_issues(url)
    #list_reviwed_issues(url)
    #list_reviwed_pr(url)
    #average_pr_close_time(url)
    #average_issue_close_time(url)
    issues, pulls = get_non_contributor_issues_and_pr(url, contributors)
    #average_pr_response_time(url)
    average_issue_response_time(url, issues, contributors)
    #lizard()

    report = "Report"
    #write_comment(git_token, repo_name, issue_number, report)
    print(report)

if __name__ == "__main__":
    main()





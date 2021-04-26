import requests
import json 
from github import Github
import sys 
import os
import datetime

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

# https://docs.github.com/en/rest/reference/pulls
# https://stackoverflow.com/questions/17423598/how-can-i-get-a-list-of-all-pull-requests-for-a-repo-through-the-github-api 
# https://stackoverflow.com/questions/18795713/parse-and-format-the-date-from-the-github-api-in-python/18795714 
# Merged implies closed, but it can be closed without being merged. Date is 'None' if it isn't merged/closed.
def average_pr_close_time(url):
    url = url + "/pulls"
    page_num = 1
    params = {"state":"all", "per_page":"100", "page":page_num}
    payload = requests.get(url=url, headers=headers, params=params).json()
    closed_durations = []
    merged_durations = []
    open_durations = []
    while len(payload) > 0:
        for it in payload:
            created_date = datetime.datetime.strptime(it["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if it["merged_at"] is not None:
                merged_date = datetime.datetime.strptime(it["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
                merged_durations.append((merged_date - created_date).total_seconds())
            elif it["closed_at"] is not None:
                closed_date = datetime.datetime.strptime(it["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
                closed_durations.append((closed_date - created_date).total_seconds())
            else:
                today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
                open_durations.append((today_formatted - created_date).total_seconds())
        page_num += 1
        params = {"state":"all", "per_page":"100", "page":page_num}
        payload = requests.get(url=url, headers=headers, params=params).json()

    average_non_merge_close_time = float(sum(closed_durations)) / (len(closed_durations))
    average_merge_time = float(sum(merged_durations)) / (len(merged_durations))
    average_still_open_time = float(sum(open_durations)) / (len(open_durations))
    print("Average time until PR closed but not merged: ", average_non_merge_close_time)
    print("Average time until PR merged: ", average_merge_time)
    print("Average time opened for still open PRs: ", average_still_open_time)

# Can probably be combined with the PR one, especially since this also has access to the pull requests
def average_issue_close_time(url):
    url = url + "/issues"
    page_num = 1
    params = {"state":"all", "per_page":"100", "page":page_num}
    payload = requests.get(url=url, headers=headers, params=params).json()
    closed_durations = []
    open_durations = []
    while len(payload) > 0:
        for it in payload:
            if "pull_request" in it:
                # 'issues' return both issues and pull requests, so we have to get rid of the pull requests
                continue
            created_date = datetime.datetime.strptime(it["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if it["closed_at"] is not None:
                closed_date = datetime.datetime.strptime(it["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
                closed_durations.append((closed_date - created_date).total_seconds())
            else:
                today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
                open_durations.append((today_formatted - created_date).total_seconds())
        page_num += 1
        params = {"state":"all", "per_page":"100", "page":page_num}
        payload = requests.get(url=url, headers=headers, params=params).json()

    average_non_merge_close_time = float(sum(closed_durations)) / (len(closed_durations))
    average_still_open_time = float(sum(open_durations)) / (len(open_durations))
    print("Average time until issue closed: ", average_non_merge_close_time)
    print("Average time opened for still open issues: ", average_still_open_time)

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
    repo_name = "EleonoraBorzis/group-validity-action" #"jhy/jsoup"
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





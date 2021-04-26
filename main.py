import requests
import json 
from github import Github
import sys 
import os
import datetime

headers = {"Accept": "application/vnd.github.v3+json"}

# Returns a bool indicating if there was at least one comment from a collaborator. If true, then a timestamp of the comment is returned as well.
# If false then the second value is None.
# The returned timestamp is of the earliest eligible comment. 
def get_first_collaborator_issue_comment(item : "json object of issue") -> "bool, datetime | None":
    collaborator_comment = False
    comment_timestamp = None
    page_num_comments = 1
    params_comments = {"per_page":"100", "page":page_num_comments}
    payload_comments = requests.get(url=item["comments_url"], headers=headers, params=params_comments).json()
    
    # "Issue Comments are ordered by ascending ID."
    # I believe this means that we are given the older ones first?
    while len(payload_comments) > 0:
        for comment in payload_comments:
            if comment["author_association"] == "COLLABORATOR" or comment["author_association"] == "OWNER":
                collaborator_comment = True
                comment_timestamp = datetime.datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                break
        if collaborator_comment:
            break
        page_num_comments += 1
        params_comments = {"per_page":"100", "page":page_num_comments}
        payload_comments = requests.get(url=item["comments_url"], headers=headers, params=params_comments).json()
    
    return collaborator_comment, comment_timestamp

# Returns a bool indicating if there was at least one comment from a collaborator. If true, then a timestamp of the comment is returned as well.
# If false then the second value is None.
# The returned timestamp is of the earliest eligible comment. 
def get_first_collaborator_pr_comment(url : str, item : "json object of pull request") -> "bool, datetime | None":
    collaborator_comment, comment_timestamp = get_first_collaborator_issue_comment(item)

    collaborator_review_comment = False
    review_comment_timestamp = None
    page_num_comments = 1
    review_url = url + "pulls/" + item["number"] + "/comments"
    params_comments = {"per_page":"100", "page":page_num_comments}
    review_comments = requests.get(url=review_url, headers=headers, params=params_comments).json()
    
    # "By default, review comments are in ascending order by ID."
    # I believe this means that we are given the older ones first?
    while len(review_comments) > 0:
        for comment in review_comments:
            if comment["author_association"] == "COLLABORATOR" or comment["author_association"] == "OWNER":
                collaborator_review_comment = True
                review_comment_timestamp = datetime.datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                break
        if collaborator_review_comment:
            break
        page_num_comments += 1
        params_comments = {"per_page":"100", "page":page_num_comments}
        review_comments = requests.get(url=review_url, headers=headers, params=params_comments).json()
    
    # Do we also count commit comments?
    if collaborator_comment and collaborator_review_comment:
        return True, min(comment_timestamp, review_comment_timestamp)
    elif collaborator_comment:
        return True, comment_timestamp
    elif collaborator_review_comment:
        return True, review_comment_timestamp
    return False, None

# Returns two lists: the first one is a list of issue that aren't created by collaborators or the owner, while the second is the respective list
# for pull requests. Note that the pull requests are not real pull requests but rather their issue representations.
def get_non_collaborator_issues_and_pr(url):
    url = url + "/issues"
    page_num = 1
    params = {"state":"all", "per_page":"100", "page":page_num}
    payload = requests.get(url=url, headers=headers, params=params).json()
    issues = []
    pull_requests = []
    while len(payload) > 0:
        for item in payload:
            if item["author_association"] == "COLLABORATOR" or item["author_association"] == "OWNER":
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


def unreviewed_issues(url):
    url = url + "/issues"
    page =1
    params = {"state":"all", "per_page":"100", "page":page}
    payload = requests.get(url=url, headers=headers, params=params).json()
    count = 0
    issues = []
    while(len(payload)>0):
        print(payload)
        for item in payload: 
            if (item["comments"] == 0):
                issues.append(str(item['number']))
                count+=1
        print(count, issues)
        print(page)
        page+=1
        params = {"state":"all", "per_page":"100", "page":page}
        payload = requests.get(url=url, headers=headers, params=params).json()
    print("The number of unreviwed issues is:" + count)
    print("The unreviwed issues are:" + issues)
    return [count, issues]


def list_reviwed_issues(url):
    print()

def list_reviwed_pr(url):
    print()

# Takes a list of either issues or pull requests as issue objects and returns the average durations of them being open
# in two categories: the ones that are closed and the ones that are still open.
# Here we don't differentiate between if a pull reqeust was only closed or also merged (merged implies closed). 
def average_close_time(issue_objects):
    closed_durations = []
    open_durations = []
    for item in issue_objects:
        created_date = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        # Date is 'None' if it isn't closed.
        if item["closed_at"] is not None:
            closed_date = datetime.datetime.strptime(item["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
            closed_durations.append((closed_date - created_date).total_seconds())
        else:
            today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
            open_durations.append((today_formatted - created_date).total_seconds())

    average_close_time = 0 if len(closed_durations) == 0 else float(sum(closed_durations)) / (len(closed_durations))
    average_still_open_time = 0 if len(open_durations) == 0 else float(sum(open_durations)) / (len(open_durations))
    # Remove print statements
    print("Average time until PR/Issue closed: ", average_close_time)
    print("Average time opened for still open PRs/Issues: ", average_still_open_time)
    return average_close_time, average_still_open_time

# The input is issues or pull requests as issue objects that are split over two lists.
# The first list consists of tuples of the issues/pull requests as well as timestamps, whereas the second list only consists of issues/pull requests.
# The parameters are inteded to be used to split issues/pull request into those that have "eligeble comments" and those that don't, 
# and then this function calculate the average time from that the issue/pull request was created until the timestamp (representing the "eligeble comment")
# for the first list, and the average time from that the issue/pull request was created until today for the second list.
def average_response_time(commented_objects, uncommented_objects):
    responded_durations = []
    not_responded_durations = []
    
    for item, comment_timestamp in commented_objects:
        created_date = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        responded_durations.append((comment_timestamp - created_date).total_seconds())

    for item in uncommented_objects:
        created_date = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        today_formatted = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
        not_responded_durations.append((today_formatted - created_date).total_seconds())

    average_responded_time = 0 if len(responded_durations) == 0 else float(sum(responded_durations)) / (len(responded_durations))
    average_not_responded_time = 0 if len(not_responded_durations) == 0 else float(sum(not_responded_durations)) / (len(not_responded_durations))
    # Remove print statement
    print("Average time until pull request is commented on by collaborator: ", average_responded_time)
    print("Average time opened for pull requests without collaborator comments: ", average_not_responded_time)
    return average_responded_time, average_not_responded_time

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
    #issue_number_to_post = sys.argv[2]
    #git_token = sys.argv[3]
    #url = "https://api.github.com/repo/" + str(repo_name)

    #dummy input
    repo_name = "EleonoraBorzis/group-validity-action" #"jhy/jsoup"
    url = "https://api.github.com/repos/" + str(repo_name)


    issues, prs = get_non_collaborator_issues_and_pr(url)
    commented_issue_list = []
    uncommented_issue_list = []
    commented_pr_list = []
    uncommented_pr_list = []
    for issue in issues:
        if issue["comments"] == 0:
            uncommented_issue_list.append(issue)
        else:
            collaborator_commented, comment_timestamp = get_first_collaborator_issue_comment(issue)
            if collaborator_commented:
                commented_issue_list.append((issue, comment_timestamp))
            else:
                uncommented_issue_list.append(issue)
    
    for pr in prs:
        if pr["comments"] == 0:
            uncommented_pr_list.append(pr)
        else:
            collaborator_commented, comment_timestamp = get_first_collaborator_pr_comment(url, pr)
            if collaborator_commented:
                commented_pr_list.append((pr, comment_timestamp))
            else:
                uncommented_pr_list.append(pr)
    
    #unreviewed_pr(url)
    #unreviewed_issues(url)
    #list_reviwed_issues(url)
    #list_unreviwed_pr(url)
    average_close_time([pr for (pr, _) in commented_pr_list] + uncommented_pr_list)
    average_close_time([issue for (issue, _) in commented_issue_list] + uncommented_issue_list)
    average_response_time(commented_pr_list, uncommented_pr_list)
    average_response_time(commented_issue_list, uncommented_issue_list)
    #lizard(True)

    report = "Report"
    #write_comment(git_token, repo_name, issue_number_to_post, report)
    print(report)

if __name__ == "__main__":
    main()





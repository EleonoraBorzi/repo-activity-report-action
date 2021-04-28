import requests
import json 
from github import Github
import sys 
import os
import datetime

headers = {"Accept": "application/vnd.github.v3+json"}
get_requests_success = True # Is set to false if any API call gets a return code other than 200

# Returns a bool indicating if there was at least one comment from a collaborator. If true, then a timestamp of the comment is returned as well.
# If false then the second value is None.
# The returned timestamp is of the earliest eligible comment. 
def get_first_collaborator_issue_comment(item : "json object of issue") -> "bool, datetime | None":
    global get_requests_success
    collaborator_comment = False
    comment_timestamp = None
    page_num_comments = 1
    params_comments = {"per_page":"100", "page":page_num_comments}
    response = requests.get(url=item["comments_url"], headers=headers, params=params_comments)

    if response.status_code != 200:
        get_requests_success = False
        return collaborator_comment, comment_timestamp
    payload_comments = response.json()
    
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
        response = requests.get(url=item["comments_url"], headers=headers, params=params_comments)
        if response.status_code != 200:
            get_requests_success = False
            return collaborator_comment, comment_timestamp
        payload_comments = response.json()
    
    return collaborator_comment, comment_timestamp

# Returns a bool indicating if there was at least one comment from a collaborator. If true, then a timestamp of the comment is returned as well.
# If false then the second value is None.
# The returned timestamp is of the earliest eligible comment. 
def get_first_collaborator_pr_comment(url : str, item : "json object of pull request") -> "bool, datetime | None":
    global get_requests_success
    collaborator_comment, comment_timestamp = get_first_collaborator_issue_comment(item)

    collaborator_review_comment = False
    review_comment_timestamp = None
    page_num_comments = 1
    review_url = url + "/pulls/" + str(item["number"]) + "/comments"
    params_comments = {"per_page":"100", "page":page_num_comments}
    response = requests.get(url=review_url, headers=headers, params=params_comments)

    if response.status_code != 200:
        get_requests_success = False
        return collaborator_comment, comment_timestamp
    review_comments = response.json()
    
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
        response = requests.get(url=review_url, headers=headers, params=params_comments)
        if response.status_code != 200:
            get_requests_success = False
            return collaborator_comment, comment_timestamp
        review_comments = response.json()
    
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
    global get_requests_success
    url = url + "/issues"
    page_num = 1
    params = {"state":"all", "per_page":"100", "page":page_num}
    response = requests.get(url=url, headers=headers, params=params)
    
    if response.status_code != 200:
        get_requests_success = False
        return [], []
    payload = response.json()

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
        response = requests.get(url=url, headers=headers, params=params)
        if response.status_code != 200:
            get_requests_success = False
            return issues, pull_requests
        payload = response.json()
    
    return issues, pull_requests

def write_comment(git_token, repo_name, issue_number, report):
    print(repo_name)
    print(issue_number)
    g = Github(git_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(issue_number))
    pr.create_issue_comment(report)

def unreviewed_pr(pr_list):
    pr_nr = []
    for item in pr_list:
        if (item["comments"] == 0):
            pr_nr.append(str(item['number']))
    report = ("The number of unreviwed issues is:" + str(len(pr_list))+ "\n")
    report = report + ("The unreviwed issues are:" + str(pr_nr) + "\n")
    return report


def unreviewed_issues(issue_list):
    issue_nr = []
    for item in issue_list:
        if (item["comments"] == 0):
            issue_nr.append(str(item['number']))
    report = ("The number of unreviwed pull requests is:" + str(len(issue_list))+ "\n")
    report = report + ("The unreviwed pull requests are:" + str(issue_nr) + "\n")
    return report


# Takes a list of either issues or pull requests as issue objects and returns the average durations of them being open
# in two categories: the ones that are closed and the ones that are still open.
# Here we don't differentiate between if a pull request was only closed or also merged (merged implies closed). 
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
    
    report = ("Average time until PR/Issue closed: " + str(average_close_time//86400) + "days" + "\n")
    report = report + ("Average time opened for still open PRs/Issues: " + str(average_still_open_time//86400) + "days"  + "\n")
    return report

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
    
    report = ("Average time until pull request is commented on by collaborator: " + str(average_responded_time//86400) + "days" +  "\n")
    report = report + ("Average time opened for pull requests without collaborator comments: " + str(average_not_responded_time//86400) + "days" +  "\n")
    return report

def lizard(include_warnings=False, head_path):
    path = os.popen("cd head_path")
    pwd = os.popen("pwd")
    print(pwd.read())
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
    git_token = sys.argv[1]
    issue_number_to_post = sys.argv[2]
    repo_name = sys.argv[3]
    
    #url = "https://api.github.com/repo/" + str(repo_name)

    #dummy input
    #repo_name = "EleonoraBorzis/group-composition-action" #"jhy/jsoup"
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
    
    head_path = "./head"
    os.mkdir(head_path)
    Repo.clone_from("https://" + git_token + "@github.com/" + repo_name + ".git", head_path, branch=main)

    report = unreviewed_pr(uncommented_pr_list)
    report = report + unreviewed_issues(uncommented_issue_list)
    report = report + average_close_time([pr for (pr, _) in commented_pr_list] + uncommented_pr_list)
    report = report + average_close_time([issue for (issue, _) in commented_issue_list] + uncommented_issue_list)
    report = report + average_response_time(commented_pr_list, uncommented_pr_list)
    report = report  + "Lizard:" + "\n" + lizard(True, head_path)


    #report = "Report"
    if not get_requests_success:
        prepend = "Some API calls to GitHub were unsuccessful, meaning this report might not include all requested data. "
        prepend += "This might have happened because of too much data being requested.\n\n"
        report = prepend + report

    
    write_comment(git_token, repo_name, issue_number_to_post, report)
    print(report)

if __name__ == "__main__":
    main()





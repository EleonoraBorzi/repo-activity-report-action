import requests
import json 
from github import Github
import sys 
import os
import datetime

with open("../access_token.txt") as f:
    t = f.readline()[:-1]
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": "token "+t} 
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

# Returns four lists: issues that have been commented, the remaning issues, pull requests that have been commented, and the remaining pull requests.
# The lists of commented issues and pull requests conssits of pairs where the first item is the issue/pull request and the second the timestamp of the comment.
# The other two lists simply consist of the issues/pull requests.
# The pull requests are treated in their issue representation.
# An issue/pull request is considered commented if it has a comment from a contributor or the owner of the repo.
# The returned timestamp is from the earliest eligible comment.
def get_commented_and_uncommmented_issues_and_preliminary_prs(url, issues, prs, repo_name):
    global get_requests_success

    review_url = url + "/issues/comments"
    page_num_comments = 1
    params_comments = {"per_page":"100", "page":page_num_comments}
    response = requests.get(url=review_url, headers=headers, params=params_comments)

    if response.status_code != 200:
        get_requests_success = False
        return [], [], [], []
    comments = response.json()
    

    commented_issues_map = {}
    commented_prs_map = {}

    while len(comments) > 0:
        for comment in comments:
            # The number isn't readily available, so we have to extract it from a link. Example: 
            # "issue_url": "https://api.github.com/repos/EleonoraBorzis/group-composition-action/issues/10",
            # Similar for both pull requests and issues
            url = comment["issue_url"]
            search_term = "issues/"
            number = int(url[url.index(search_term) + len(search_term) : ])
            
            # Similarly it isn't readily available if it is an issue or a pull request. Example:
            # "html_url": "https://github.com/EleonoraBorzis/group-composition-action/pull/10#issuecomment-810912871",
            url = comment["html_url"]
            start_index = url.index(repo_name) + len(repo_name) + 1 # +1 to account for following slash
            item_type = url[start_index : start_index + 4]

            if comment["author_association"] == "COLLABORATOR" or comment["author_association"] == "OWNER":
                new_timestamp = datetime.datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")

                if item_type == "pull":
                    if number in commented_prs_map:
                        previous_timestamp = commented_prs_map[number]
                        commented_prs_map[number] = min(previous_timestamp, new_timestamp)
                    else:
                        commented_prs_map[number] = new_timestamp

                else:
                    if number in commented_issues_map:
                        previous_timestamp = commented_issues_map[number]
                        commented_issues_map[number] = min(previous_timestamp, new_timestamp)
                    else:
                        commented_prs_map[number] = new_timestamp

        page_num_comments += 1
        params_comments = {"per_page":"100", "page":page_num_comments}
        response = requests.get(url=review_url, headers=headers, params=params_comments)
        if response.status_code != 200:
            get_requests_success = False
            return [], [], [], []
        comments = response.json()

    commented_issues = []
    uncommented_issues = []
    commented_prs = []
    uncommented_prs = []

    for issue in issues:
        if issue["number"] in commented_issues_map:
            commented_issues.append((issue, commented_issues_map[issue["number"]]))
        else:
            uncommented_issues.append(issue)
    
    for pr in prs:
        if pr["number"] in commented_prs_map:
            commented_prs.append((pr, commented_prs_map[pr["number"]]))
        else:
            uncommented_prs.append(pr)

    return commented_issues, uncommented_issues, commented_prs, uncommented_prs

# Optimized for when the amount of review comments is much larger than the amount of pull requests.
def get_commented_and_uncommmented_issues(url, issues):
    commented_issue_list = []
    uncommented_issue_list = []
    for issue in issues:
        if issue["comments"] == 0:
            uncommented_issue_list.append(issue)
        else:
            collaborator_commented, comment_timestamp = get_first_collaborator_issue_comment(issue)
            if collaborator_commented:
                commented_issue_list.append((issue, comment_timestamp))
            else:
                uncommented_issue_list.append(issue)
    return commented_issue_list, uncommented_issue_list

# Returns two list, the first with all pull request that have been commented on by a contributor or the owner, and the second list is the remaining pull requests.
# The first returned list is of pairs where the first object is the pull request and the second is the first timestamp of an eligible comment.
# The second reutrned lsit si simple pull request objects.
# The pull requests are in their issue json representation (both in arguments and in return). 
def get_commented_and_uncommented_prs(url, commented_prs, uncommented_prs):
    global get_requests_success

    review_url = url + "/pulls/comments"
    page_num_comments = 1
    params_comments = {"per_page":"100", "page":page_num_comments}
    response = requests.get(url=review_url, headers=headers, params=params_comments)

    if response.status_code != 200:
        get_requests_success = False
        return [], []
    review_comments = response.json()
    
    commented_prs_map = {}
    for pr, timestamp in commented_prs:
        commented_prs_map[pr["number"]] = timestamp

    while len(review_comments) > 0:
        for comment in review_comments:
            # The number isn't readily available, so we have to extract it from a link
            pr_url = comment["pull_request_url"]
            search_term = "pulls/"
            pr_number = int(pr_url[pr_url.index(search_term) + len(search_term) : ])
            if comment["author_association"] == "COLLABORATOR" or comment["author_association"] == "OWNER":
                new_timestamp = datetime.datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if pr_number in commented_prs_map:
                    previous_timestamp = commented_prs_map[pr_number]
                    commented_prs_map[pr_number] = min(previous_timestamp, new_timestamp)
                else:
                    commented_prs_map[pr_number] = new_timestamp

        page_num_comments += 1
        params_comments = {"per_page":"100", "page":page_num_comments}
        response = requests.get(url=review_url, headers=headers, params=params_comments)
        if response.status_code != 200:
            get_requests_success = False
            return [], []
        review_comments = response.json()

    ret_commented = []
    ret_uncommented = []

    for pr in uncommented_prs:
        if pr["number"] in commented_prs_map:
            ret_commented.append((pr, commented_prs_map[pr["number"]]))
        else:
            ret_uncommented.append(pr)
    for pr,_ in commented_prs:
        ret_commented.append((pr, commented_prs_map[pr["number"]]))

    return ret_commented, ret_uncommented

# Optimized for when the amount of review comments is much larger than the amount of pull requests.
def get_commented_and_uncommented_prs_alternative(url, prs):
    commented_pr_list = []
    uncommented_pr_list = []
    for pr in prs:
        if pr["comments"] == 0:
            uncommented_pr_list.append(pr)
        else:
            collaborator_commented, comment_timestamp = get_first_collaborator_pr_comment(url, pr)
            if collaborator_commented:
                commented_pr_list.append((pr, comment_timestamp))
            else:
                uncommented_pr_list.append(pr)
    return commented_pr_list, uncommented_pr_list


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
    g = Github(git_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(issue_number)
    pr.create_issue_comment(report)

def unreviewed_pr(pr_list):
    pr_nr = []
    for item in pr_list:
        if (item["comments"] == 0):
            pr_nr.append(str(item['number']))
    report = ("The number of unreviwed issues is:" + str(len(pr_list))+ "\n")
    report = report + ("The unreviwed issues are:" + str(pr_nr) + "\n")
    return (pr_nr, report)


def unreviewed_issues(issue_list):
    issue_nr = []
    for item in issue_list:
        if (item["comments"] == 0):
            issue_nr.append(str(item['number']))
    report = ("The number of unreviwed issues is:" + str(len(issue_list))+ "\n")
    report = report + ("The unreviwed issues are:" + str(issue_nr) + "\n")
    return (issue_nr, report)


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
    # Remove print statements
    print("Average time until PR/Issue closed: ", average_close_time)
    print("Average time opened for still open PRs/Issues: ", average_still_open_time)
    return average_close_time, average_still_open_time

# The input is issues or pull requests as issue objects that are split over two lists.
# The first list consists of tuples of the issues/pull requests as well as timestamps, whereas the second list only consists of issues/pull requests.
# The parameters are inteded to be used to split issues/pull request into those that have "eligible comments" and those that don't, 
# and then this function calculate the average time from that the issue/pull request was created until the timestamp (representing the "eligible comment")
# for the first list, and the average time from that the issue/pull request was created until today for the second list.
def average_response_time(commented_objects, uncommented_objects):
    responded_durations = []
    not_responded_durations = []
    
    for item, comment_timestamp in commented_objects:
        created_date = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        responded_durations.append((comment_timestamp - created_date).total_seconds())

    for item in uncommented_objects:
        created_date = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if item["closed_at"] is None:
            end_date = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%dT%H:%M:%SZ")
        else:
            end_date = datetime.datetime.strptime(item["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
        not_responded_durations.append((end_date - created_date).total_seconds())

    average_responded_time = 0 if len(responded_durations) == 0 else float(sum(responded_durations)) / (len(responded_durations))
    average_not_responded_time = 0 if len(not_responded_durations) == 0 else float(sum(not_responded_durations)) / (len(not_responded_durations))
    # Remove print statement
    print("Average time until issue/pull request is commented on by collaborator: ", average_responded_time)
    print("Average time opened for issues/pull requests without collaborator comments: ", average_not_responded_time)
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
    repo_name = "KTH/devops-course" #"EleonoraBorzis/group-composition-action" #"jhy/jsoup"
    url = "https://api.github.com/repos/" + str(repo_name)


    issues, prs = get_non_collaborator_issues_and_pr(url)
    commented_issue_list, uncommented_issue_list, preliminary_commented_pr_list, preliminary_uncommented_pr_list = get_commented_and_uncommmented_issues_and_preliminary_prs(url, issues, prs, repo_name)
    commented_pr_list, uncommented_pr_list = get_commented_and_uncommented_prs(url, preliminary_commented_pr_list, preliminary_uncommented_pr_list)

    (pr_list, report)=unreviewed_pr(uncommented_pr_list)
    (issue_list, report) = unreviewed_issues(uncommented_issue_list)
    average_close_time([pr for (pr, _) in commented_pr_list] + uncommented_pr_list)
    average_close_time([issue for (issue, _) in commented_issue_list] + uncommented_issue_list)
    average_response_time(commented_pr_list, uncommented_pr_list)
    average_response_time(commented_issue_list, uncommented_issue_list)
    #lizard(True)

    report = "Report"
    if not get_requests_success:
        prepend = "Some API calls to GitHub were unsuccessful, meaning this report might not include all requested data. "
        prepend += "This might have happened because of too much data being requested.\n\n"
        report = prepend + report
    #write_comment(git_token, repo_name, issue_number_to_post, report)
    print(report)

if __name__ == "__main__":
    main()





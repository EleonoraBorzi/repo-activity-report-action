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

def unreviewed_pr(url):
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
    try:
        while(page<2):
        #while (len(payload) > 0):
            print(payload)
            for item in payload: 
                if (item["comments"] == 0):
                    issues.append(str(item['number']))
                    count+=1
            print(count, issues)
            print(page)
            page+=1
            payload = requests.get(url=url, headers=headers, params=params).json()
        print("The number of unreviwed issues is:" + count)
        print("The unreviwed issues are:" + issues)
        return [count, issues]
    except:
        print("The number of unreviwed issues is:", count)
        print("The unreviwed issues are:", issues)
        return [count, issues]
    
    

def average_pr_close_time(url):
    print()

def average_issue_close_time(url):
    print()

def average_pr_response_time(url):
    print()

def average_issue_response_time(url):
    print()

# def lizard():
#     stream = os.popen("lizard")
#     output = stream.read()
#     print("lizard:\n")
#     print(output)

def main():
    #repo_name = sys.argv[1]
    #issue_number = sys.argv[2]
    #git_token = sys.argv[3]
    #url = "https://api.github.com/repo/" + str(repo_name)

    #dummy input
    repo_name = "jhy/jsoup"
    url = "https://api.github.com/repos/" + str(repo_name)

    #unreviewed_pr(url)
    issues = unreviewed_issues(url)
    average_pr_close_time(url)
    average_issue_close_time(url)
    average_pr_response_time(url)
    average_issue_response_time(url)
    #lizard()

    report = "Report"
    #write_comment(git_token, repo_name, issue_number, report)
    print(report)

if __name__ == "__main__":
    main()





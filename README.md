# GitHub Action for activity and complexity monitoring

This github action can be use to analyse the activity and the Code Complexity of a repo. It is wrapped in a Docker container, allowing it to easily be used by other workflows. When triggered, a python script will run, making calls to the GitHub API to measure activity and utilizing [lizard](https://pypi.org/project/lizard/) for measuring code complexity.

The action will post a comment on the specified Issue/PR with all the generated data. Below there is a code that shows how to use the action in a workflow yaml file:

```yaml
name: Report Activity Test
on:
  schedule:
    - cron: '0 8 30 * *'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: EleonoraBorzis/repo-activity-report-action@main
        with: 
          github-token: ${{ secrets.GITHUB_TOKEN }}
          repo-name:  EleonoraBorzis/group-composition-action
          issue-number: 10
```

The action has three inputs:
- github-token: The GitHub secret token that gives access to several git functions. It also increases the limit of GitHub API calls. 
- repo-name: The full name of the repo that is being analysed.
- issue-number: The number of the issue where the user wants the report to be posted as a comment.

The user can decide how the action will be triggered, for example a new pull request or at a set day every month. The action will post a comment on the issue with the issue number given by the user. The data posted on the action is: 
- The number of unreviwed issues 
- A list of unreviwed issues
- The number of unreviwed pull requests 
- A list of unreviwed pull requests 
- Average time until PR/Issue closed
- Average time of how long PR/Issues that are still open have been open
- Average time until pull request is commented on by collaborator
- Average time opened for pull requests without collaborator comments
- Lizard output (ex. NLOC, CCN, token, PARAM, length, etc)

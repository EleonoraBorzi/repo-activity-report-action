# repo-activity-report-action

This github action can be use to analyse the activity and the Code Complexity of a repo. It is implemented with Docker, so it is mor accessible to the public, and it uses a python script. The data analysed is:

- The number of unreviwed issues 
- A list of unreviwed issues
- The number of unreviwed pull requests 
- A list of unreviwed pull requests 
- Average time until PR/Issue closed
- Average time opened for still open PRs/Issues
- Average time until pull request is commented on by collaborator
- Average time opened for pull requests without collaborator comments
- Lizard output (ex. NLOC, CCN, token, PARAM, length, etc)

The action will post a comment on the specified Issue/PR with all the data listed above. Here is an example of a comment:

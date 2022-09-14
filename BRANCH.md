For managing our fork, there are primarily 3 branches we will be working with.

1. upstream/master - This is the upstream package that we want to get all our public improvements in eventually
2. main - This is our internal shadow of upstream/master, it should be 1:1. This is what we should make branches off of for changes we want to go upstream
3. onboard-main - This is our final copy of digital buildings with all of the upstream changes, pending upstream changes, and any other changes that aren't compatible with the upstream/master

Workflow for making improvements:
1. Branch off of main
2. make changes
3. pull-request into upstream/master

Upon acceptance and merge, we will update our internal main and subsequently update our onboard-main. If there are changes we NEED in onboard-main, we can accelerate part of the cycle and pull-request into onboard-main at the same time as we PR into upstream/master. When it does get accepted, it should result in a noop merge and everything will be healthy again. But complications will arise if changes get made to the PR after the PR lands in onboard-main, hence this not being the standard workflow.

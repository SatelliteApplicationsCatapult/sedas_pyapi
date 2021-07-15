# Release Process

This is a note for future releases so we know what to do.

1) Create a new branch prep-<version to be released>
1) Update the version number in setup.py
1) Add the release to the top of the HISTORY.md file
1) Push through a pull request with these changes to master.
1) Check out master on your machine
1) If this is the first time you've done a release on this machine run `python3 -m pip install --user --upgrade twine`
1) Run `make dist`
1) Run `python3 -m twine upload dist/*` It will ask for your pipy user name and password.
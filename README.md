# g-workspaces-scripts
Random useful scripts for interacting with Google Workspaces

Setup on Ubuntu looks similar to the following:
```
$ sudo apt install python3-virtualenv
$ cd
$ virtualenv gdrive-search
$ cd gdrive-search
$ source bin/activate
$ pip install google-api-python-client
```

Follow the links at: https://developers.google.com/drive/api/v3/quickstart/python to setup a google cloud platform project with the API enabled (Drive API) AND how to "Create credentials" to put credentials.json and token.json in-place

## findAugmentedPerms_SharedDrive.py
Take in a shared drive driveID and give you a list of files / folders that have augmented permissions, including a report of all permissions that are NOT inherited. This script needs credentials saved in credentials.json for it to operate. An optional "folders-only" mode is also available for cases where a file-by-file audit is not necessary. 

Output looks similar to the following:
```
$ python findAugmentedPerms_SharedDrive.py --driveID [ID# found in your URL] --folders-only
NOTICE: ONLY Folders will be examined!

Files / Folders with Augmented Permissions:

FILE-OR-FOLDER-NAME
----
Permissions granted...
  Role: writer
  User-Email: email@your-org.com
  Permission Inherited: False

  Role: reader
  User-Email: email2@your-org.com
  Permission Inherited: False

  Role: fileOrganizer
  User-Email: email3@your-org.com
  Permission Inherited: False

FILE-OR-FOLDER-NAME-2
----
Permissions granted...
  Role: writer
  User-Email: email@your-org.com
  Permission Inherited: False
```

from __future__ import print_function
import argparse
import os.path
#import pprint
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Useful reading...
# https://developers.google.com/drive/api/v3/quickstart/python
# https://developers.google.com/workspace/guides/create-credentials
# https://developers.google.com/drive/api/v3/search-files
# https://developers.google.com/drive/api/v3/reference/files
# https://developers.google.com/drive/api/v3/shared-drives-diffs
# https://developers.google.com/drive/api/v3/ref-search-terms
# https://developers.google.com/drive/api/v3/fields-parameter

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
# NOTE driveID must match the ID of the shared drive that you want to search.
# Clicking on the shared drive in the web interface will show you the ID in the
# url bar.
driveID="none"


def parse_args():
    """Parse command line arguments and return a namespace object."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--driveID',
        required=True,
        help='ID of the shared drive to search',
    )
    parser.add_argument(
        '--user-email',
        required=True,
        help='Email address of a user you would like removed from permission to items.',
    )
    parser.add_argument(
        '--folders-only',
        action='store_true',
        help='only examine folders (not individual files)',
    )
    parser.add_argument(
        '--do-it',
        action='store_true',
        help='Really rip out the permissions... BE CAREFUL - Run a test job first!!!!',
    )
    return parser.parse_args()


def main(driveID, userEmail, foldersOnly, doIt):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    print("\nWARNING!!!!")
    print("THIS SCRIPT WILL NOT CLEAR USERS FROM FOLDERS WHERE THEY HAVE THE")
    print("FILE ORGANIZER OR ORGANIZER SHARED DRIVE ROLE")
    print("IT ALSO WILL NOT CLEAR PERMISSIONS THAT ARE INHERITED\n")
    creds = None
    foundAugmentedFile=False
    queryOptions = ''
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Call the Drive v3 API
    service = build('drive', 'v3', credentials=creds)

    if(foldersOnly):
        queryOptions = 'mimeType=\'application/vnd.google-apps.folder\' and ' + queryOptions
    else:
        queryOptions = queryOptions
    
    # Handle the userEmail
    if not re.match(r'[^@]+@[^@]+\.[^@]+', userEmail):
        print("INVALID EMAIL PROVIDED!")
        quit()
    # Limit our file / folder results to just those that show the supplied user as having access to the file
    # Search results will also be limited to folders, if that option is enabled
    queryOptions = queryOptions + '\'' + userEmail + '\'' + ' in readers'
    results = service.files().list(
        q=queryOptions,
        pageSize=1000,
        corpora='drive',
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        driveId=driveID,
        fields="nextPageToken, files(id, name, hasAugmentedPermissions, permissions/*)").execute()
# Enable the below to see ALL file properties (for debugging)
#        fields="*").execute()
    token = results.get('nextPageToken', None)
    items = results.get('files', [])
    while token is not None:
        results = service.files().list(
                q=queryOptions,
                pageSize=1000,
                corpora='drive',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageToken=token,
                driveId=driveID,
                fields="nextPageToken, files(id, name, hasAugmentedPermissions, permissions/*)").execute()
# Enable the below to see ALL file properties (for debugging)
#                fields="*").execute()
        token = results.get('nextPageToken', None)
        items.extend(results.get('files', []))

    if not items:
        print('No files found.')
    else:
        print('Files / Folders with Augmented Permissions with user ' + userEmail + ':\n')
        for item in items:
            if item['hasAugmentedPermissions']:
                foundAugmentedFile=True
                print(u'{0}'.format(item['name']))
                print('----')
                # Enable the below to see all available fields for the located file / folder
                # pprint.pp(item)

                # Get a permission listing for the item
                permissions = service.permissions().list(fileId=item['id'], supportsAllDrives=True,fields="*").execute()
                print("Permissions granted...")

                # Enable the below to see all permissions details for the located file / folder 
                # pprint.pp(permissions)
                foundItem = False
                for perm in permissions['permissions']:
                    # Enable the bbelow to see all permission details for the permission item
                    # pprint.pp(perm)
                    try:
                        if (perm['permissionDetails'][0]['inherited'] == False and perm['emailAddress'] == userEmail):
                            foundItem = True
                            if(doIt):
                                print(" --do-it ENABLED: REMOVING PERMISSION!")
                                service.permissions().delete(fileId=item['id'], supportsAllDrives=True,permissionId=perm['id']).execute()
                            else:
                                print("IF --do-it was passed I would execute:")
                                print("service.permissions().delete(fileId=" + item['id'] + ", supportsAllDrives=True,permissionId=" + perm['id'] + ").execute()")
                            print("  Role: " + perm['role'])
                            print("  User-Email: " + perm['emailAddress'])
                            print("  Permission Inherited: " + str(perm['permissionDetails'][0]['inherited']) + "\n")
                    except KeyError:
                        print("  WARNING!! NO EMAIL FOUND! LIKELY A LINK SHARING SCENARIO WARNING!!!")
                        # If the below is enabled, show what's up with the funky permission object 
                        # pprint.pp(perm['permissionDetails'][0]['inherited'])
                    try:    
                        if not perm['permissionDetails'][1]['inherited']:
                            foundItem = True
                            print("  Shared Drive override and file permissions found...")
                            print("  If this is the only permission entry, this file is likely safe to ignore\n")
#                            pprint.pp(perm)
                    except IndexError:
                        ignoreMe = 1
                    except KeyError:
                        ignoreMe = 1
                if not foundItem:
                    print("  Unknown permissions")
        if foundAugmentedFile == False:
            print('No files with Augmented Permissions found')


if __name__ == '__main__':
    args = parse_args()
    if args.folders_only:
        print("NOTICE: ONLY Folders will be examined!\n")
    main(args.driveID, args.user_email, args.folders_only, args.do_it)

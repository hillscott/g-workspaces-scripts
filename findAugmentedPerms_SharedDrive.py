from __future__ import print_function
import os.path
import sys
#import pprint
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Useful reading...
# https://developers.google.com/drive/api/v3/quickstart/python
# https://developers.google.com/workspace/guides/create-credentials
# https://developers.google.com/drive/api/v2/search-files
# https://developers.google.com/drive/api/v2/reference/files
# https://developers.google.com/drive/api/v2/shared-drives-diffs
# https://developers.google.com/drive/api/v2/ref-search-terms
# https://developers.google.com/drive/api/v3/fields-parameter

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
# NOTE driveID must match the ID of the shared drive that you want to search.
# Clicking on the shared drive in the web interface will show you the ID in the
# url bar.
driveID="none"

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    if("--driveID" in sys.argv):
        driveID = sys.argv[sys.argv.index("--driveID") + 1]
    else:
        print("ERROR: No --driveID passed! Find the shared drive ID!")
        quit()
    if("--folders-only" in sys.argv):
        print("ONLY Folders will be examined!")
        foldersOnly = True
    else:
        foldersOnly=False
    creds = None
    foundAugmentedFile=False
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
        queryOptions = 'mimeType=\'application/vnd.google-apps.folder\''
    else:
        queryOptions = ''
    results = service.files().list(
        q=queryOptions,
        pageSize=1000, 
        corpora='drive', 
        includeItemsFromAllDrives=True, 
        supportsAllDrives=True, 
        driveId=driveID, 
        fields="nextPageToken, files(id, name, hasAugmentedPermissions, permissions/*)").execute()
# Enable the below to see ALL file properties    
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
# Enable the below to see ALL file properties        
#                fields="*").execute()
        token = results.get('nextPageToken', None)
        items.extend(results.get('files', []))

    if not items:
        print('No files found.')
    else:
        print('Files / Folders with Augmented Permissions:')
        for item in items:
            if item['hasAugmentedPermissions']:
                foundAugmentedFile=True
                print(u'{0}'.format(item['name']))
#                pprint.pp(item)
                # Get a permission listing for the item
                permissions = service.permissions().list(fileId=item['id'], supportsAllDrives=True,fields="*").execute()
                print("Permissions granted...")
#                pprint.pp(permissions)
                foundItem = False
                for perm in permissions['permissions']:
#                    pprint.pp(perm)
                    if not perm['permissionDetails'][0]['inherited']:
                        foundItem = True
                        print("  Role: " + perm['role'])
                        try:
                            print("  User-Email: " + perm['emailAddress'])
                        except KeyError:
                            print("  WARNING!! NO EMAIL FOUND! LIKELY A LINK SHARING SCENARIO WARNING!!!")
#                        pprint.pp(perm['permissionDetails'][0]['inherited'])
                        print("  Permission Inherited: " + str(perm['permissionDetails'][0]['inherited']) + "\n")
                if not foundItem:
                    print("  Unknown permissions")
        if foundAugmentedFile == False:
            print('No files with Augmented Permissions found')
if __name__ == '__main__':
    main()

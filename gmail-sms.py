# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# pip install smtp

from __future__ import print_function
import datetime
import pickle
import base64
import smtplib
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from email.mime.text import MIMEText

scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def checkCred():
    creds = None
    
    if os.path.exists('/home/pi/gmail-sms/token.pickle'):
        with open('/home/pi/gmail-sms/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/home/pi/gmail-sms/credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('/home/pi/gmail-sms/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def main():
    service = checkCred()
    results = service.users().messages().list(userId='me',labelIds = ['INBOX'], q="is:unread").execute()
    messages = results.get('messages', []) 
        
    with open("/home/pi/gmail-sms/run.log", mode='a') as file:
        file.write('Printed string %s recorded at %s.\n' % 
                   ("attempt", datetime.datetime.now())
    )
    file.close()
    if not messages:
        print("No messages found.")
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            print(msg['snippet'])
            if ", on your upcoming stay!" in msg['snippet']:
                msg_body = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
                msg_str = base64.urlsafe_b64decode(msg_body['raw'].encode('ASCII'))

                res_date = (msg_str.split(b'Your access will be active for the duration of your stay:')[1]).split(b'\r\n')[1]
                checkout_date = res_date.split(b'to ')[1].decode("utf-8")
                clean_date = checkout_date.replace(" 11:00 AM.", "")
                print(clean_date)

                msg = '''Cleaning requested: {}'''.format(clean_date)
                # Establish a secure session with gmail's outgoing SMTP server using your gmail account
                server = smtplib.SMTP( "smtp.gmail.com", 587 )
                server.starttls()
                server.login( 'email-address', 'email-password' )

                # Send text message through SMS gateway of destination number                
                server.sendmail( '<phone-from>', '<phone-to>@mms.att.net', msg )
                service.users().messages().modify(userId='me', id=message['id'], body={
                    'removeLabelIds': ['UNREAD']
                }).execute()

                with open("/home/pi/gmail-sms/run.log", mode='a') as file:
                    file.write('Printed string %s recorded at %s.\n' % 
                               (msg, datetime.datetime.now())
                )
                file.close()
                
         
if __name__ == '__main__':
    main()

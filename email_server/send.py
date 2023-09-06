#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on  22/4/23 19:29

@author: Edward L. Campbell Hernández
contact: ecampbelldsp@gmail.com
"""
from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow



import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


import base64
import mimetypes
import os
from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
def oauth_init():
    SCOPES = ['https://mail.google.com/']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('credentials/token.json'):
        creds = Credentials.from_authorized_user_file('credentials/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('credentials/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
def gmail_send_message(FROM = None, TO = None, attachment_filename = None, message_text="", subject = 'Automated draft'):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    for guides on implementing OAuth2 for the application.
    """
    # creds, _ = google.auth.default()
    creds = oauth_init()
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(message_text)

        message['To'] = TO
        message['From'] = FROM
        message['Subject'] = subject

        # attachment
        # attachment_filename = att
        # guessing the MIME type


        if attachment_filename is not None:
            type_subtype, _ = mimetypes.guess_type(attachment_filename)
            maintype, subtype = type_subtype.split('/')
            with open(attachment_filename, 'rb') as fp:
                attachment_data = fp.read()
            message.add_attachment(attachment_data, maintype, subtype, filename = attachment_filename.split("/")[-1])

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = False
    return send_message


if __name__ == '__main__':
    os.chdir("../")
    # gmail_send_message(FROM = 'opencheckdoc@gmail.com' , TO ="ecampbelldsp@gmail.com", att = '')
    gmail_send_message(FROM = 'apartamentoselsquimics@gmail.com' , TO ="ecampbelldsp@gmail.com", attachment_filename = "C:/Opencheck/tmp/9032979507951.zip", message_text = "Automatic draft message", subject="TEST")
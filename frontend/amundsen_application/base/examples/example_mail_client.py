# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http import HTTPStatus
from typing import Dict, List

from flask import Response, jsonify, make_response

from amundsen_application.base.base_mail_client import BaseMailClient


#  based on https://stackoverflow.com/a/6270987
class MailClient(BaseMailClient):
    def __init__(self, recipients: List[str]) -> None:
        self.recipients = recipients

    def send_email(self,
                   html: str,
                   subject: str,
                   optional_data: Dict = None,
                   recipients: List[str] = None,
                   sender: str = None) -> Response:
        if not sender:
            sender = os.environ.get('AMUNDSEN_EMAIL') or ''  # set me
        if not recipients:
            recipients = self.recipients

        sender_pass = os.environ.get('AMUNDSEN_EMAIL_PASSWORD') or ''  # set me

        # Create message container - the correct MIME type
        # to combine text and html is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        # Record the MIME type of text/html
        # and attach parts to message container.
        msg.attach(MIMEText(html, 'html'))

        s = smtplib.SMTP('smtp.gmail.com')
        try:
            s.connect('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(sender, sender_pass)
            message = s.send_message(msg)
            payload = jsonify({'msg': message})
            s.quit()
            return make_response(payload, HTTPStatus.OK)
        except Exception as e:
            err_message = 'Encountered exception: ' + str(e)
            logging.exception(err_message)
            payload = jsonify({'msg': err_message})
            s.quit()
            return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)

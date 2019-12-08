import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from pathlib import Path
import mimetypes
import re
from typing import List

class mail_media:
    def __init__(self, filepath_or_binary, cid=None, binary_mode=False, filename=None):
        if not binary_mode:
            self.media_mode = 'path'
            self.filepath_or_binary = Path(filepath_or_binary)

            if not self.filepath_or_binary.is_file():
                raise Exception('this is not a file')

            try:
                pass
                c = self.filepath_or_binary.stem if cid is None else cid
            except TypeError:
                c = None

            if c is None:
                c = 'undefined',

        else:
            if filename is None:
                raise Exception('filename required in binary mode')

            self.media_mode = 'binary'
            self.filepath_or_binary = filepath_or_binary

            c = cid if cid is not None else 'undefined'

        self.filename = filename
        self.cid = c


class mail_sender:
    def __init__(self, _from, _to):
        self._from = _from
        self.str_from = _from.addr_spec

        self._to = _to
        self.str_to = tuple((x.addr_spec for x in _to))

        self.msg_root = EmailMessage()
        self.msg_root['From'] = self.str_from
        self.msg_root['To'] = self.str_to

    def create_message(self, subject='', message='', media=[], attachments=[]):
        self.msg_root['Subject'] = subject
        self.msg_root.add_alternative(message, subtype='html')

        if not isinstance(attachments, list):
            if isinstance(attachments, mail_media):
                attachments = [attachments, ]
            else:
                raise TypeError('attachments deve ser mail_media ou uma lista de mail_medias')

        if not isinstance(media, list):
            if isinstance(media, mail_media):
                media = [media, ]
            else:
                raise TypeError('media deve ser mail_media ou uma lista de mail_medias')

        for m in media:
            if m.media_mode == 'path':
                maintype, subtype = mimetypes.guess_type(m.filepath_or_binary.name)[
                    0].split('/')
                with open(m.filepath_or_binary, 'rb') as kek:
                    self.msg_root.get_payload()[0].add_related(
                        kek.read(), maintype=maintype,
                        subtype=subtype,
                        cid=m.cid)
            else:
                maintype, subtype = mimetypes.guess_type(m.filename)[
                    0].split('/')
                self.msg_root.get_payload()[0].add_related(
                    m.filepath_or_binary, maintype=maintype,
                    subtype=subtype,
                    cid=m.cid)

        for a in attachments:
            part = MIMEBase('application', 'octet-stream')
            if a.media_mode == 'path':
                with open(a.filepath_or_binary, 'rb') as kek:
                    part.set_payload(kek.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename={a.filepath_or_binary.name}')
            else:
                part.set_payload(a.filepath_or_binary)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                f'attachment; filename={a.filename}')
            self.msg_root.attach(part)

        return self

    def send(self, smtp_addr, smtp_port, tls=True, enable_auth=True, username='', password=''):
        smtp = smtplib.SMTP(smtp_addr, smtp_port)
        if tls:
            smtp.ehlo()
            smtp.starttls()
        if enable_auth:
            smtp.login(username, password)
        smtp.sendmail(self.str_from, self.str_to, self.msg_root.as_string())
        smtp.quit()

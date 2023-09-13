import io
import base64
import mimetypes
import os
from email.mime import audio, base, image, text, multipart
from email import encoders
from apiclient import errors
import pandas as pd
from .config import GoogleAuthentication


class Gmail(GoogleAuthentication):
    service_type = 'gmail'
    accepted_domains = ['shopee.com', 'airpay.com', 'seagroup.com', 'ved.com.vn']

    def __init__(self, service_type=service_type):
        super().__init__(service_type)

    def create_message(self, to, subject, message_text, files=None, cc=None, inline_image=None, sender="me"):
        """Create a message for an email.

      Args:
        sender: Email address of the sender, default="me"
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        files: The path to the file to be attached. type = list
        cc: CC mail

      Returns:
        An object containing a base64url encoded email object.
        :param inline_image:
      """
        message = multipart.MIMEMultipart('mixed')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        message['Cc'] = cc

        # inline image:

        if inline_image:
            for i, image in enumerate(inline_image, 1):
                message_text += f'<br><img src="cid:image{i}">'
                msgImage = file_for_attach_mail(image)
                msgImage.add_header('Content-ID', f'<image{i}>')

                # message.attach(MIMEText(message_text, 'html'))
                message.attach(msgImage)
            message.attach(text.MIMEText(message_text, 'html'))
        else:
            message.attach(text.MIMEText(message_text, 'html'))

        if files:
            if not isinstance(files, list):
                files = [files]
            print(f"send mail with attach files: {files}")
            for file in files:
                msg = file_for_attach_mail(file)
                if file.split('.')[-1]:
                    if file.split('.')[-1] == 'xlsx':
                        msg = base.MIMEBase('application', "vnd.ms-excel")
                        msg.set_payload(open(file, "rb").read())
                        encoders.encode_base64(msg)
                    else:
                        msg = base.MIMEBase('application', "octet-stream")
                        msg.set_payload(open(file, "rb").read())
                        encoders.encode_base64(msg)
                else:
                    msg = file_for_attach_mail(file)
                filename = os.path.basename(file)
                msg.add_header('Content-Disposition', 'attachment', filename=filename)

                message.attach(msg)

        # return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    def send_message(self, message, user_id="me"):
        """Send an email message.
      Args:
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

      Returns:
        Sent Message.
      """
        try:
            message = (self.service.users().messages().send(userId=user_id, body=message).execute())
            print(f"Message Id: {message['id']}")
            return message
        except errors.HttpError as error:
            print(f"An error occurred: {error}")

    def send_mail(self, to, subject, message_text, files=None, cc=None, inline_img=None, sender="me", user_id="me"):
        """
        send gmail ex: send_mail('edward.nguyen@shopee.com', 'test', 'hello world', ['daily.zip'])
        :param to: address of the receiver
        :param subject: email subject
        :param message_text: content
        :param files: attach files, default: None
        :param cc: Cc email, default: None
        :param sender: sender address, default: "me"
        :param user_id: default: "me"
        :return: sent email
        """

        message = self.create_message(to=to, subject=subject, message_text=message_text, files=files, cc=cc,
                                      sender=sender, inline_image=inline_img)
        self.send_message(message, user_id=user_id)
        print(f"Sent mail: to {to}, subject: {subject} !!")

    def search_single_message(self, query):
        """
            Searching email
            :param query: input your query
            :return: first item from result list
            """
        message_info = self.service.users().messages().list(userId='me', q=query).execute()
        try:
            print(f"executed query: {message_info['messages'][0]['id']}")
            return message_info['messages'][0]['id']
        except Exception as e:
            print(e)
            return None

    def ListMessagesMatchingQuery(self, query, user_id='me'):
        """List all Messages of the user's mailbox matching the query.

        Args:
          user_id: User's email address. The special value "me"
          can be used to indicate the authenticated user.
          query: String used to filter messages returned.
          Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

        Returns:
          List of Messages that match the criteria of the query. Note that the
          returned list contains Message IDs, you must use get with the
          appropriate ID to get the details of a Message.
        """
        try:
            response = self.service.users().messages().list(userId=user_id, q=query).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self.service.users().messages().list(userId=user_id, q=query,
                                                                pageToken=page_token).execute()
                messages.extend(response['messages'])

            return messages
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    # @classmethod
    def download_one_from_email(self, messageId, directory, filename):
        file_names = []
        file_path = ''
        try:
            message = self.service.users().messages().get(userId='me', id=messageId).execute()
            for part in message['payload']['parts']:
                if part['filename'] == filename:
                    # data = part['body'].get('data')
                    attachmentId = part['body'].get('attachmentId')
                    attachment_info = self.service.users().messages().attachments().get(userId='me', id=attachmentId,
                                                                                        messageId=messageId).execute()
                    data = attachment_info['data']
                    file_path = directory + part['filename']
                    file_type = part['filename'].split('.')[1]
                    if file_type == 'csv':
                        f = open(file_path, 'wb')
                        f.write(base64.urlsafe_b64decode(data.encode('UTF-8')))
                        f.close()
                    elif file_type == 'xlsx':
                        decrypted = base64.urlsafe_b64decode(data.encode('UTF-8'))
                        toread = io.BytesIO()
                        toread.write(decrypted)
                        df = pd.read_excel(toread)
                        df.to_excel(file_path, index=None)
                    file_names.append(file_path)
            if len(file_names) > 1:
                return file_names
            return file_path

        except errors.HttpError as error:
            print(f'An error occurred: {str(error)}')
            return None

    # @classmethod
    def download_all_from_email(self, messageId, directory):
        file_names = []
        try:
            message = self.service.users().messages().get(userId='me', id=messageId).execute()
            file_path = ''
            for part in message['payload']['parts']:
                if part['filename']:
                    # data = part['body'].get('data')
                    attachmentId = part['body'].get('attachmentId')
                    attachment_info = self.service.users().messages().attachments().get(userId='me', id=attachmentId,
                                                                                        messageId=messageId).execute()
                    data = attachment_info['data']
                    file_path = f"{directory}/{part['filename']}"
                    file_type = part['filename'].split('.')[1]
                    if file_type == 'csv':
                        f = open(file_path, 'wb')
                        f.write(base64.urlsafe_b64decode(data.encode('UTF-8')))
                        f.close()
                    elif file_type == 'xlsx':
                        decrypted = base64.urlsafe_b64decode(data.encode('UTF-8'))
                        toread = io.BytesIO()
                        toread.write(decrypted)
                        df = pd.read_excel(toread)
                        df.to_excel(file_path, index=None)
                    file_names.append(file_path)
            if len(file_names) > 1:
                return file_names
            return file_path

        except errors.HttpError as error:
            print(f'An error occurred: {error}')
            return None


def file_for_attach_mail(file):
    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    print(main_type)
    if main_type == 'text':
        fp = open(file, 'rb')
        msg = text.MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(file, 'rb')
        msg = image.MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(file, 'rb')
        msg = audio.MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(file, 'rb')
        msg = base.MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()

    return msg

import io
from colorama import Fore
import mimetypes
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .config import GoogleAuthentication


class Drive(GoogleAuthentication):
    service_type = 'drive'

    def __init__(self, service_type=service_type):
        super().__init__(service_type)
        self.status = f'{Fore.LIGHTRED_EX}🦑 Drive:{Fore.RESET}'

    def upload(self, file_dir, name_on_drive: str, folder_id: str):
        """Upload to drive"""
        file_metadata = {'name': name_on_drive, 'parents': [folder_id]}
        content_type, _ = mimetypes.guess_type(file_dir)
        media = MediaFileUpload(file_dir, mimetype=content_type)
        fields = 'webContentLink, id, webViewLink'
        file = self.service.files().create(body=file_metadata, media_body=media, fields=fields).execute()
        print(f"{self.status} upload file_id: {file.get('id')} folder_id: {folder_id}")
        return file

    def get_file_info(self, file_id):
        return self.service.files().get(fileId=file_id).execute()

    def drive_download(self, file_id, download_dir):
        file_info = self.get_file_info(file_id)
        request = self.service.files().get_media(fileId=file_id)
        download_name = file_info['name']
        save_path = f"{download_dir}/{download_name}"
        fh = io.FileIO(save_path, 'wb')  # save to somewhere with name...
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%!")

        return save_path

    def create_new_folder(self, name, parent_id=None, return_id=False):
        """
        create new folder on Google Drive
        :param name: Name of folder
        :param parent_id: id of parent folder , default None
        :param return_id: return folder id if True
        :return: return folder id if True
        """

        file_metadata = {
            'name': name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if not parent_id:
            file_metadata.pop('parents')
        file = self.service.files().create(body=file_metadata,
                                           fields='id').execute()
        print(f"Successfully created folder: {name}   Folder ID: {file.get('id')}")

        if return_id:
            return file.get('id')

    def rename_drive_file(self, spreadsheet_id, new_name):
        file = {'name': new_name}
        self.service.files().update(fileId=spreadsheet_id, body=file).execute()

    def download_gsheet(self, file_id, file_location, file_name, file_type):
        request = self.service.files().export_media(fileId=file_id, mimeType=file_type)
        fh = io.FileIO(file_location + file_name, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

    def search_files(self, folder_id):
        fields = 'nextPageToken, files(id, name, createdTime, modifiedTime)'
        results = self.service.files().list(q=f"'{folder_id}' in parents and trashed=false", fields=fields).execute()
        return results.get('files', [])

    def share_publicly(self, file_id):
        user_permission = {'type': 'anyone', 'role': 'reader'}
        reponse = self.service.permissions().create(fileId=file_id, body=user_permission, fields='id').execute()
        print(f"{self.status} share publicly at file: {file_id} {reponse.get('id')}")

    def remove_share_publicly(self, file_id):
        self.service.permissions().delete(fileId=file_id, permissionId='anyoneWithLink', fields='id').execute()
        print(f"{self.status} remove share publicly at file: {file_id}")

import boto3
import os
from colorama import Fore
from pathlib import Path
from tqdm import tqdm
from google.cloud import storage
import datetime


class AWS:
    def __init__(self, bucket_name: str):
        dict_ = {
            'endpoint_url': 'https://s3g.data-infra.shopee.io',
            'aws_access_key_id': os.environ['PRESTO_USER'],
            'aws_secret_access_key': os.environ['PRESTO_PASSWORD'],
        }
        self.bucket_name = bucket_name
        self.client = boto3.client('s3', **dict_)
        self.my_bucket = boto3.resource('s3', **dict_).Bucket(self.bucket_name)
        self.status = f'{Fore.LIGHTCYAN_EX}🐸 S3:{Fore.RESET}'

    def get_file_size(self, key: str):
        return self.my_bucket.Object(key).content_length

    def upload_file(self, file: Path):
        file_size = file.stat().st_size
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=f'Upload - {file.name}') as pbar:
            self.my_bucket.upload_file(
                file,
                Key=file.stem,
                Callback=lambda x: pbar.update(x))
        print(f'{self.status} Upload file successfully')

    def download_file(self, path: Path, key: str):
        file_size = self.get_file_size(key)
        with tqdm(total=file_size, unit="B", unit_scale=True, desc=f'Download - {key}') as pbar:
            self.my_bucket.download_file(
                Key=key,
                Filename=path / key,
                Callback=lambda x: pbar.update(x),
            )
        print(f'{self.status} Download file successfully')

    def create_presigned_url(self, key: str, expiration: int = 900):
        url = self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expiration
        )
        print(f'{self.status} Presigned [{key}] in {expiration / 3600}h')
        return url


class Gcloud:
    def __init__(self, json_path: str):
        path = Path.home() / json_path
        self.client = storage.Client.from_service_account_json(str(path))
        self.status = f'{Fore.LIGHTBLUE_EX}🐻‍❄️ Gcloud:{Fore.RESET}'
        self.bucket_name = 'kevin-bi'
        self.bucket = self.client.bucket(self.bucket_name)

    def download_file(self, blob_path: str, file_path: Path):
        blob = self.bucket.blob(blob_path)
        blob.download_to_filename(file_path)
        print(f'{self.status} download {blob_path}')

    def upload_file(self, blob_path: str, file_path: Path):
        blob_path_full = f'{blob_path}/{file_path.name}'
        blob = self.bucket.blob(blob_path_full)
        blob.upload_from_filename(file_path)
        print(f'{self.status} upload {file_path.stem} to {blob_path}')
        return blob_path_full

    def generate_download_signed_url_v4(self, blob_file, minutes=15):
        blob = self.bucket.blob(blob_file)
        url = blob.generate_signed_url(
            version='v4',
            expiration=datetime.timedelta(minutes=minutes),
            method='GET',
            response_type='image/png',
        )
        print(f'{self.status} Presigned [{blob_file}] in {minutes} mins')
        return url

from colorama import Fore
from collections import defaultdict
from .config import GoogleAuthentication
from .GDrive import Drive


class Slide(GoogleAuthentication):
    service_type = 'slides'

    def __init__(self, presentationId: str, service_type=service_type):
        super().__init__(service_type)
        self.pre_id = presentationId
        self.status = f'{Fore.LIGHTYELLOW_EX}🐱 Slides:{Fore.RESET}'
        self.all_info = self.service.presentations().get(presentationId=self.pre_id).execute().get('slides')
        self.slide_idx = {idx: slide.get('objectId') for idx, slide in enumerate(self.all_info, start=1)}

    def duplicate_slide(self, num_slide: int):
        requests = [
            {'duplicateObject': {'objectId': self.slide_idx.get(num_slide), 'objectIds': {}}}
        ]
        body = {'requests': requests}
        self.service.presentations().batchUpdate(presentationId=self.pre_id, body=body).execute()
        print(f'{self.status} duplicate slide {num_slide}')

    def create_image(self, url: str, num_slide: int, size: dict, position: dict):
        requests = [
            {
                'createImage': {
                    'elementProperties': {
                        'pageObjectId': self.slide_idx.get(num_slide),
                        'size': size,
                        'transform': position
                    },
                    'url': url
                }
            }
        ]
        body = {'requests': requests}
        self.service.presentations().batchUpdate(presentationId=self.pre_id, body=body).execute()
        print(f"{self.status} created a image at slide {num_slide}")

    def delete_object(self, object_id):
        requests = [{'deleteObject': {'objectId': object_id,}}]
        body = {'requests': requests}
        self.service.presentations().batchUpdate(presentationId=self.pre_id, body=body).execute()
        print(f"{self.status} remove a object {object_id}")

    def replace_images_by_drive(self, img_path, num_slide: int, size: dict, position: dict):
        """drive folder_id is fixed"""
        # upload by Drive
        drive = Drive()
        folder_id = '1jO-tbvoIyqeJcXD2EmgWSkSZMFc-fMCn'  # media folder
        file_upload = drive.upload(file_dir=img_path, name_on_drive='test', folder_id=folder_id)
        file_upload_id = file_upload.get('id')

        # permission
        drive.share_publicly(file_id=file_upload_id)
        url = f"https://drive.google.com/uc?export=view&id={file_upload_id}"
        self.create_image(url=url, num_slide=num_slide, size=size, position=position)

        # remove permission
        drive.remove_share_publicly(file_upload_id)
        print(f"{self.status} replace a image at slide {num_slide}")

    def get_slide_object_image(self, num_slide):
        img_dict = defaultdict(dict)
        info = self.all_info[num_slide - 1]
        for i in info.get('pageElements'):
            objectid = i.get('objectId')
            position = i.get('transform')
            size = i.get('size')
            if img_url := i.get('image', {}).get('contentUrl'):
                img_dict[objectid].update({'url': img_url, 'position': position, 'size': size})
        print(f"{self.status} get image objects at slide {num_slide}")
        return img_dict

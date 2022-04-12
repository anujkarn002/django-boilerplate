import boto3

from botocore.client import Config

from django.conf import settings

from rest_framework.generics import RetrieveAPIView
from rest_framework.exceptions import ParseError

from .utils import success_response


class FileUploadView(RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        region_name = settings.AWS_S3_REGION_NAME
        signature_version = 's3v4'
        filename = request.GET.get('file', '')
        if not filename:
            raise ParseError(detail='Querystring file not provided')
        s3_client = boto3.client('s3', config=Config(
            signature_version=signature_version, region_name=region_name))
        upload_details = s3_client.generate_presigned_post(
            bucket_name, f'media/public/{filename}', Fields={"acl": "public-read", }, Conditions=[
                {"acl": "public-read"},
            ])
        return success_response(detail="Generated pre-signed post", **upload_details)

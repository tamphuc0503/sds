import boto3
from botocore.config import Config
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Copy pdf import links from crawler (sdsadmin) to our system."

    def add_arguments(self, parser):
        parser.add_argument("size", nargs="?", type=int)
        parser.add_argument("use_queue", nargs="?", type=bool)

    def handle(self, *args, **options):
        worker_name = "import_contabo"
        files = self._list_files_by_paginator("sds", "s1")
        print(files)

    def _get_s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url="https://usc1.contabostorage.com",
            aws_access_key_id="f35256d14c2a22f4648bce44896529d8",
            aws_secret_access_key="7672dbe85d3e540b7c62ff6df5704ef3",
            region_name="usc1",
            config=Config(s3={"addressing_style": "path"}),  # important for Contabo
        )

    def _list_files_by_paginator(self, bucket_name, sub_path=""):
        files = []
        page_count = 0
        paginator = self._get_s3_client().get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=bucket_name,
            Prefix=sub_path,
            PaginationConfig={"PageSize": 10000},  # 👈 page size control
        ):
            page_count += 1
            # for obj in page.get("Contents", []):
            #     files.append(obj["Key"])
            #     if len(files) > 10000:
            #         break

        return files

    def _list_s3_files(self, bucket_name, subpath=""):
        s3 = self._get_s3_client()

        params = {
            "Bucket": bucket_name,
            "Prefix": subpath,  # 👈 important
            "MaxKeys": 10000,
        }
        response = s3.list_objects_v2(params)

        files = []

        if "Contents" in response:
            for obj in response["Contents"]:
                files.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                    }
                )

        return files

    def _list_files(self):
        bucket_name = "sds"
        files = self._list_s3_files(bucket_name)
        return files

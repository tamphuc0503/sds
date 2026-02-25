import os
import boto3
from botocore.config import Config
from django.core.management.base import BaseCommand

from extractions.models import SdsFile


class Command(BaseCommand):
    help = "Copy pdf from S3 Contabo"

    def add_arguments(self, parser):
        parser.add_argument("size", nargs="?", type=int)
        parser.add_argument("use_queue", nargs="?", type=bool)

    def handle(self, *args, **options):
        worker_name = "import_contabo"
        token = self._read_token()
        
        # Loop through all pages until no more token
        page_count = 0
        total_files = 0
        max_pages = 50000
        
        while True:
            page_count += 1
            
            # Safety break at 10000 pages
            if page_count > max_pages:
                self.stdout.write(self.style.WARNING(f"Reached maximum page limit ({max_pages}). Stopping."))
                break
            
            self.stdout.write(f"Processing batch {page_count}/{max_pages}...")
            
            files, token = self._list_files_resume_from_token("sds", "s1", token)
            
            if not files:
                self.stdout.write(self.style.WARNING("No more files to process"))
                break
            
            # Insert files into database
            self.bulk_insert_sdsfiles(files)
            total_files += len(files)
            self.stdout.write(self.style.SUCCESS(f"  Inserted {len(files)} files (Total: {total_files})"))
            
            # Save token for resuming later
            if token:
                self._save_token(token)
            else:
                self.stdout.write(self.style.SUCCESS("All files processed!"))
                break
        
        self.stdout.write(self.style.SUCCESS(f"Completed! Total batches: {page_count}, Total files: {total_files}"))

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
        """
        List all files from S3 bucket using paginator.
        This automatically handles pagination through all results.
        """
        files = []
        page_count = 0

        paginator = self._get_s3_client().get_paginator("list_objects_v2")

        # Paginate through all pages automatically
        for page in paginator.paginate(
            Bucket=bucket_name,
            Prefix=sub_path,
            PaginationConfig={"PageSize": 1000},  # Number of items per page
        ):
            page_count += 1
            self.stdout.write(f"Processing page {page_count}...")

            # Get contents from current page
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                            "etag": obj.get("ETag", "").strip('"'),  # MD5 hash
                        }
                    )

                self.stdout.write(
                    f"  Found {len(page['Contents'])} files in page {page_count}"
                )

        self.stdout.write(
            self.style.SUCCESS(f"Total: {len(files)} files across {page_count} pages")
        )

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

    def _list_files_resume_from_token(self, bucket_name, prefix="", start_token=None):
        """
        Resume pagination from a specific point using a token.
        Useful for processing large datasets in chunks.
        """
        s3 = self._get_s3_client()
        files = []
        next_token = start_token

        paginator = s3.get_paginator("list_objects_v2")

        config = {"PageSize": 100}
        if next_token:
            config["StartingToken"] = next_token

        page_iterator = paginator.paginate(
            Bucket=bucket_name, Prefix=prefix, PaginationConfig=config
        )

        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(obj["Key"])

            # Save token to resume later
            if "NextContinuationToken" in page:
                next_token = page["NextContinuationToken"]
                print(f"Next token: {next_token}")

            return files, next_token

    def _read_token(self):
        try:
            with open("contabo_token.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def _save_token(self, token):
        with open("contabo_token.txt", "w") as f:
            f.write(token)

    def bulk_insert_sdsfiles(self, files):
        """
        Bulk insert multiple SdsFile records

        Args:
            data_list: List of dictionaries with SdsFile data
            Example: [
                {
                    'md5': 'abc123',
                    'file_path': '/path/1',
                    'md5_content': 'xyz789',
                    'content': 'Content 1',
                    'version_date': date(2026, 2, 24),
                    'version_date_str': '2026-02-24'
                },
                ...
            ]
        """
        sds_files = [
            SdsFile(
                md5=self._get_md5_from_file_path(file),
                file_path=file,
            )
            for file in files
        ]

        # bulk_create is much faster than saving individually
        created_instances = SdsFile.objects.bulk_create(sds_files)
        return created_instances

    def _get_md5_from_file_path(self, file_path: str):
        full_filename = os.path.basename(file_path)
        filename, _ = full_filename.rsplit(".", 1)
        return filename

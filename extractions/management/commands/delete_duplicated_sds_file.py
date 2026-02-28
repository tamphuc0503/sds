import os
import boto3
from botocore.config import Config
from django.core.management.base import BaseCommand

from extractions.models import SdsFile


class Command(BaseCommand):
    help = "Delete duplicated sds files"

    def add_arguments(self, parser):    
        parser.add_argument("size", nargs="?", type=int)
        parser.add_argument("use_queue", nargs="?", type=bool)

    def handle(self, *args, **options):
        worker_name = "delete_duplicated_sds_file"
        
        # Get files marked as deleted
        deleted_files = self._get_files_marked_deleted()
        
        if not deleted_files:
            self.stdout.write(self.style.WARNING("No files marked as deleted found"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Found {len(deleted_files)} files marked as deleted"))
        
        # Process each file
        deleted_count = 0
        failed_count = 0
        
        for idx, sds_file in enumerate(deleted_files, 1):
            self.stdout.write(f"\n[{idx}/{len(deleted_files)}] Processing: {sds_file.file_path}")
            
            try:
                # Delete from S3
                s3_deleted = self._delete_from_s3(sds_file.file_path)
                
                if s3_deleted:
                    # Delete from database
                    file_path = sds_file.file_path
                    md5 = sds_file.md5
                    sds_file.delete()
                    
                    deleted_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Deleted from S3 and database: {file_path} (md5={md5})"
                    ))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"  ✗ Failed to delete from S3, skipping database deletion"
                    ))
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"Summary:\n"
            f"  Total files processed: {len(deleted_files)}\n"
            f"  Successfully deleted: {deleted_count}\n"
            f"  Failed: {failed_count}\n"
            f"{'='*60}"
        ))
    
    def _get_files_marked_deleted(self, limit=2000000):
        """
        Get list of SdsFile records marked as deleted (is_deleted=True).
        
        Args:
            limit: Maximum number of records to retrieve (default: 1000)
            
        Returns:
            QuerySet: List of SdsFile objects marked as deleted
        """
        files = SdsFile.objects.filter(is_deleted=True)[:limit]
        return list(files)
    
    def _delete_from_s3(self, file_path, bucket_name="sds"):
        """
        Delete a file from S3 Contabo storage.
        
        Args:
            file_path: The path/key of the file in S3
            bucket_name: The S3 bucket name (default: 'sds')
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        s3 = self._get_s3_client()
        
        try:
            self.stdout.write(f"  Deleting from S3: {file_path}...")
            s3.delete_object(Bucket=bucket_name, Key=file_path)
            self.stdout.write(f"  Successfully deleted from S3")
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error deleting from S3: {e}"))
            return False

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
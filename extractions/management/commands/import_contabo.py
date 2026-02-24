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
        while(i < 10):
            token = self._read_token()
            files, token = self._list_files_resume_from_token("sds", "s1", token)
            i= i+1
            self._save_token(token)
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
                    files.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "etag": obj.get("ETag", "").strip('"'),  # MD5 hash
                    })
                
                self.stdout.write(f"  Found {len(page['Contents'])} files in page {page_count}")
        
        self.stdout.write(self.style.SUCCESS(
            f"Total: {len(files)} files across {page_count} pages"
        ))
        
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
        s3 = self._get()
        files = []
        next_token = start_token
        
        paginator = s3.get_paginator("list_objects_v2")
        
        config = {"PageSize": 10}
        if next_token:
            config["StartingToken"] = next_token
        
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix=prefix,
            PaginationConfig=config
        )
        
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(obj["Key"])
            
            # Save token to resume later
            if "NextToken" in page:
                next_token = page["NextToken"]
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
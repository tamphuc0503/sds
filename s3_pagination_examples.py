"""
Examples of S3 pagination patterns using boto3
"""

import boto3
from botocore.config import Config


def get_s3_client():
    """Initialize S3 client for Contabo"""
    return boto3.client(
        "s3",
        endpoint_url="https://usc1.contabostorage.com",
        aws_access_key_id="YOUR_ACCESS_KEY",
        aws_secret_access_key="YOUR_SECRET_KEY",
        region_name="usc1",
        config=Config(s3={"addressing_style": "path"}),
    )


# ============================================================================
# 1. BASIC PAGINATOR - Iterate through all pages automatically
# ============================================================================

def list_all_files_paginator(bucket_name, prefix=""):
    """
    Use paginator to automatically iterate through all pages.
    This is the RECOMMENDED approach for listing all files.
    """
    s3 = get_s3_client()
    files = []
    
    # Create paginator
    paginator = s3.get_paginator("list_objects_v2")
    
    # Paginate automatically iterates through ALL pages
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj.get("ETag", "").strip('"'),  # MD5 hash
                })
    
    return files


# ============================================================================
# 2. PAGINATOR WITH PAGE SIZE CONTROL
# ============================================================================

def list_files_with_page_size(bucket_name, prefix="", page_size=1000):
    """
    Control how many items are returned per page.
    The paginator still handles all pages automatically.
    """
    s3 = get_s3_client()
    files = []
    page_count = 0
    
    paginator = s3.get_paginator("list_objects_v2")
    
    # PaginationConfig controls the page size
    for page in paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig={"PageSize": page_size}
    ):
        page_count += 1
        print(f"Processing page {page_count}...")
        
        if "Contents" in page:
            for obj in page["Contents"]:
                files.append(obj["Key"])
            print(f"  Found {len(page['Contents'])} files")
    
    print(f"Total: {len(files)} files from {page_count} pages")
    return files


# ============================================================================
# 3. PAGINATOR WITH MAX ITEMS LIMIT
# ============================================================================

def list_files_with_limit(bucket_name, prefix="", max_items=5000):
    """
    Stop after retrieving a maximum number of items.
    Useful when you don't need all files.
    """
    s3 = get_s3_client()
    files = []
    
    paginator = s3.get_paginator("list_objects_v2")
    
    # MaxItems limits total items across all pages
    page_iterator = paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig={"MaxItems": max_items, "PageSize": 1000}
    )
    
    for page in page_iterator:
        if "Contents" in page:
            for obj in page["Contents"]:
                files.append(obj["Key"])
    
    return files


# ============================================================================
# 4. PAGINATOR WITH STARTING TOKEN (Resume pagination)
# ============================================================================

def list_files_resume_from_token(bucket_name, prefix="", start_token=None):
    """
    Resume pagination from a specific point using a token.
    Useful for processing large datasets in chunks.
    """
    s3 = get_s3_client()
    files = []
    next_token = start_token
    
    paginator = s3.get_paginator("list_objects_v2")
    
    config = {"PageSize": 1000}
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


# ============================================================================
# 5. MANUAL PAGINATION (without paginator)
# ============================================================================

def list_files_manual_pagination(bucket_name, prefix=""):
    """
    Manually handle pagination using ContinuationToken.
    More control but requires manual loop management.
    """
    s3 = get_s3_client()
    files = []
    continuation_token = None
    page_count = 0
    
    while True:
        page_count += 1
        
        # Build request parameters
        params = {
            "Bucket": bucket_name,
            "Prefix": prefix,
            "MaxKeys": 1000,
        }
        
        # Add continuation token if we have one
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        
        # Make the request
        response = s3.list_objects_v2(**params)
        
        # Process results
        if "Contents" in response:
            for obj in response["Contents"]:
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                })
            print(f"Page {page_count}: {len(response['Contents'])} files")
        
        # Check if there are more pages
        if response.get("IsTruncated"):
            continuation_token = response.get("NextContinuationToken")
        else:
            break  # No more pages
    
    return files


# ============================================================================
# 6. PROCESS FILES AS YOU ITERATE (Memory efficient)
# ============================================================================

def process_files_streaming(bucket_name, prefix=""):
    """
    Process files as you iterate instead of loading all into memory.
    Best for very large buckets.
    """
    s3 = get_s3_client()
    total_count = 0
    total_size = 0
    
    paginator = s3.get_paginator("list_objects_v2")
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                # Process each file immediately
                total_count += 1
                total_size += obj["Size"]
                
                # Example: Filter PDF files
                if obj["Key"].endswith(".pdf"):
                    print(f"Found PDF: {obj['Key']}")
                
                # Example: Process every 1000 files
                if total_count % 1000 == 0:
                    print(f"Processed {total_count} files so far...")
    
    print(f"Total: {total_count} files, {total_size / (1024**3):.2f} GB")
    return {"count": total_count, "size": total_size}


# ============================================================================
# 7. PAGINATOR WITH FILTERS (Using JMESPath)
# ============================================================================

def list_files_with_filter(bucket_name, prefix="", min_size=0):
    """
    Filter results using JMESPath expressions during pagination.
    """
    s3 = get_s3_client()
    files = []
    
    paginator = s3.get_paginator("list_objects_v2")
    
    # You can also use JMESPath to filter on the server side
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                # Client-side filtering
                if obj["Size"] > min_size:
                    files.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                    })
    
    return files


# ============================================================================
# 8. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    bucket = "sds"
    prefix = "s1"
    
    # Basic usage - get all files
    # files = list_all_files_paginator(bucket, prefix)
    # print(f"Found {len(files)} files")
    
    # With page size control
    # files = list_files_with_page_size(bucket, prefix, page_size=500)
    
    # With limit
    # files = list_files_with_limit(bucket, prefix, max_items=1000)
    
    # Resume from token
    # files, next_token = list_files_resume_from_token(bucket, prefix)
    # More pages? files2, token2 = list_files_resume_from_token(bucket, prefix, next_token)
    
    # Manual pagination
    # files = list_files_manual_pagination(bucket, prefix)
    
    # Streaming (memory efficient)
    # stats = process_files_streaming(bucket, prefix)
    
    # With filters
    # files = list_files_with_filter(bucket, prefix, min_size=1024*1024)  # > 1MB
    
    pass

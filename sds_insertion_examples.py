"""
Examples for inserting and bulk inserting data into the SdsFile table
"""

from datetime import date, datetime
from extractions.models import SdsFile

# ============================================================================
# 1. SINGLE INSERT - Create a new SdsFile instance
# ============================================================================

def insert_single_sdsfile():
    """Insert a single SdsFile record"""
    sds_file = SdsFile(
        md5='abc123def456',
        file_path='/path/to/file.sds',
        md5_content='xyz789',
        content='File content here...',
        version_date=date(2026, 2, 24),
        version_date_str='2026-02-24'
    )
    sds_file.save()
    return sds_file


# ============================================================================
# 2. SINGLE INSERT - Using create() method
# ============================================================================

def insert_single_sdsfile_create():
    """Insert a single SdsFile record using create()"""
    sds_file = SdsFile.objects.create(
        md5='def789ghi012',
        file_path='/path/to/another/file.sds',
        md5_content='abc456',
        content='Another file content...',
        version_date=date(2026, 2, 24),
        version_date_str='2026-02-24'
    )
    return sds_file


# ============================================================================
# 3. BULK INSERT - Using bulk_create()
# ============================================================================

def bulk_insert_sdsfiles(data_list):
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
            md5=data['md5'],
            file_path=data['file_path'],
            md5_content=data['md5_content'],
            content=data['content'],
            version_date=data['version_date'],
            version_date_str=data['version_date_str']
        )
        for data in data_list
    ]
    
    # bulk_create is much faster than saving individually
    created_instances = SdsFile.objects.bulk_create(sds_files)
    return created_instances


# ============================================================================
# 4. BULK INSERT WITH BATCH SIZE
# ============================================================================

def bulk_insert_with_batch(data_list, batch_size=1000):
    """
    Bulk insert with batch size for very large datasets
    
    Args:
        data_list: List of dictionaries with SdsFile data
        batch_size: Number of records to insert per batch (default 1000)
    """
    sds_files = [
        SdsFile(
            md5=data['md5'],
            file_path=data['file_path'],
            md5_content=data['md5_content'],
            content=data['content'],
            version_date=data['version_date'],
            version_date_str=data['version_date_str']
        )
        for data in data_list
    ]
    
    created_instances = SdsFile.objects.bulk_create(
        sds_files,
        batch_size=batch_size
    )
    return created_instances


# ============================================================================
# 5. BULK INSERT WITH IGNORE_CONFLICTS (Skip duplicates)
# ============================================================================

def bulk_insert_ignore_conflicts(data_list):
    """
    Bulk insert with ignore_conflicts=True
    Skips records that would violate unique constraints (e.g., duplicate md5)
    
    Args:
        data_list: List of dictionaries with SdsFile data
    """
    sds_files = [
        SdsFile(
            md5=data['md5'],
            file_path=data['file_path'],
            md5_content=data['md5_content'],
            content=data['content'],
            version_date=data['version_date'],
            version_date_str=data['version_date_str']
        )
        for data in data_list
    ]
    
    # ignore_conflicts will skip duplicates (based on unique constraints)
    SdsFile.objects.bulk_create(
        sds_files,
        ignore_conflicts=True
    )


# ============================================================================
# 6. BULK UPDATE OR CREATE (Upsert)
# ============================================================================

def bulk_update_or_create(data_list):
    """
    Update existing records or create new ones
    Uses get_or_create for each record
    
    Args:
        data_list: List of dictionaries with SdsFile data
    """
    created_count = 0
    updated_count = 0
    
    for data in data_list:
        # get_or_create looks for matching md5 and creates if not found
        sds_file, created = SdsFile.objects.get_or_create(
            md5=data['md5'],
            defaults={
                'file_path': data['file_path'],
                'md5_content': data['md5_content'],
                'content': data['content'],
                'version_date': data['version_date'],
                'version_date_str': data['version_date_str']
            }
        )
        
        if created:
            created_count += 1
        else:
            # Update existing record
            sds_file.file_path = data['file_path']
            sds_file.md5_content = data['md5_content']
            sds_file.content = data['content']
            sds_file.version_date = data['version_date']
            sds_file.version_date_str = data['version_date_str']
            sds_file.save()
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


# ============================================================================
# 7. BULK UPDATE OR CREATE (Efficient batch version)
# ============================================================================

def bulk_update_or_create_batch(data_list):
    """
    More efficient upsert using bulk operations
    
    Args:
        data_list: List of dictionaries with SdsFile data
    """
    existing_mds = set(SdsFile.objects.values_list('md5', flat=True))
    
    to_create = []
    to_update = []
    
    for data in data_list:
        sds_file = SdsFile(
            md5=data['md5'],
            file_path=data['file_path'],
            md5_content=data['md5_content'],
            content=data['content'],
            version_date=data['version_date'],
            version_date_str=data['version_date_str']
        )
        
        if data['md5'] in existing_mds:
            to_update.append(sds_file)
        else:
            to_create.append(sds_file)
    
    # Bulk create new records
    if to_create:
        SdsFile.objects.bulk_create(to_create)
    
    # Bulk update existing records
    if to_update:
        SdsFile.objects.bulk_update(
            to_update,
            fields=[
                'file_path',
                'md5_content',
                'content',
                'version_date',
                'version_date_str'
            ]
        )
    
    return {'created': len(to_create), 'updated': len(to_update)}


# ============================================================================
# 8. EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Example data
    sample_data = [
        {
            'md5': 'hash001',
            'file_path': '/files/doc1.sds',
            'md5_content': 'content001',
            'content': 'This is document 1',
            'version_date': date(2026, 2, 24),
            'version_date_str': '2026-02-24'
        },
        {
            'md5': 'hash002',
            'file_path': '/files/doc2.sds',
            'md5_content': 'content002',
            'content': 'This is document 2',
            'version_date': date(2026, 2, 24),
            'version_date_str': '2026-02-24'
        },
        {
            'md5': 'hash003',
            'file_path': '/files/doc3.sds',
            'md5_content': 'content003',
            'content': 'This is document 3',
            'version_date': date(2026, 2, 24),
            'version_date_str': '2026-02-24'
        },
    ]
    
    # Single insert
    # single = insert_single_sdsfile()
    # print(f"Single insert: {single}")
    
    # Bulk insert
    # bulk = bulk_insert_sdsfiles(sample_data)
    # print(f"Bulk inserted: {len(bulk)} records")
    
    # Bulk insert with batch size
    # bulk_batch = bulk_insert_with_batch(sample_data, batch_size=500)
    # print(f"Bulk inserted (batch): {len(bulk_batch)} records")

import hashlib
import os
import re
import boto3
from botocore.config import Config
from django.core.management.base import BaseCommand
import fitz  # PyMuPDF
from langdetect import detect, LangDetectException
from extractions.models import SdsFile

class Command(BaseCommand):
    help = "Check md5 content and assign to md5_content from S3 Contabo"

    def add_arguments(self, parser):
        parser.add_argument("size", nargs="?", type=int)
        parser.add_argument("use_queue", nargs="?", type=bool)

    def handle(self, *args, **options):        
        worker_name = "assign_md5_content"
        
        # Get list of files with null md5_content
        files_to_process = self._get_files_with_null_md5_content(limit=10000)
        
        if not files_to_process:
            self.stdout.write(self.style.WARNING("No files found with null md5_content"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Found {len(files_to_process)} files to process"))
        
        # Process each file
        for idx, sds_file in enumerate(files_to_process, 1):
            self.stdout.write(f"\n[{idx}/{len(files_to_process)}] Processing: {sds_file.file_path}")            
            self._process_file(sds_file.file_path)           
        
        self.stdout.write(self.style.SUCCESS(f"\nCompleted processing {len(files_to_process)} files"))
    
    def _process_file(self, file_path):
        try:
            # Download file from S3
            local_file_path = self.download_file_from_s3(file_path)
            
            if local_file_path is not None:
                try:
                    cur_md5 = get_md5_from_file_path(local_file_path)
                    md5 = calculate_md5(local_file_path)
                    
                    if cur_md5 == md5:
                        # Process and update database
                        self.stdout.write(self.style.HTTP_INFO(f"Downloaded {local_file_path} with md5 {md5}"))
                        self._assign_md5_content(md5, local_file_path)
                    else:
                        # MD5 mismatch
                        self.stdout.write(self.style.ERROR(f"MD5 mismatch: expected {cur_md5}, got {md5}"))                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing file: {e}"))
                finally:
                    if os.path.exists(local_file_path):
                        self._delete_local_file(local_file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading {file_path}: {e}"))

            
    def _get_files_with_null_md5_content(self, limit=1000):
        """
        Get list of SdsFile records where md5_content is null.
        
        Args:
            limit: Maximum number of records to retrieve (default: 1000)
            
        Returns:
            QuerySet: List of SdsFile objects with null md5_content
        """
        files = SdsFile.objects.filter(md5_content__isnull=True)[:limit]
        return list(files)
            
    def _assign_md5_content(self, md5, local_file_path):
        """
        Process PDF to extract content and update SdsFile record.
        
        Args:
            md5: The MD5 hash of the file (used as identifier)
            local_file_path: Path to the downloaded PDF file
        """
        try:
            # Process PDF to get md5_content, cleaned text, and language
            result = process_pdf_to_md5(local_file_path)
            md5_content = result['md5_hash']
            content = result['cleaned_text']
            language = result.get('language')  # May be None if detection failed
            
            # Update SdsFile record where md5 matches
            update_fields = {
                'md5_content': md5_content,
                'content': content,
            }
            
            # Only update language if it was detected
            if language:
                update_fields['language'] = language
            
            updated_count = SdsFile.objects.filter(md5=md5).update(**update_fields)
            
            if updated_count > 0:
                lang_msg = f", language={language}" if language else ""
                self.stdout.write(self.style.SUCCESS(
                    f"Updated {updated_count} record(s) for md5={md5} with md5_content={md5_content}{lang_msg}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"No records found with md5={md5}"
                ))
            
            return updated_count
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Error processing PDF for md5={md5}: {e}"
            ))
            raise
    
    def _delete_local_file(self, file_path):
        """
        Delete a local file after processing.
        
        Args:
            file_path: Path to the local file to delete
            
        Returns:
            bool: True if file was deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.stdout.write(self.style.SUCCESS(f"Deleted local file: {file_path}"))
                return True
            else:
                self.stdout.write(self.style.WARNING(f"File not found, cannot delete: {file_path}"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting file {file_path}: {e}"))
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

    def download_file_from_s3(self, s3_file_path, local_file_path=None, bucket_name="sds"):
        """
        Download a file from S3 Contabo storage.
        
        Args:
            s3_file_path: The path/key of the file in S3 (e.g., 's1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf')
            local_file_path: Optional local path to save the file. If not provided, saves to current directory with same filename
            bucket_name: The S3 bucket name (default: 'sds')
            
        Returns:
            str: The local file path where the file was saved
            
        Example:
            # Download to current directory
            self.download_file_from_s3('s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf')
            
            # Download to specific path
            self.download_file_from_s3('s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf', '/tmp/myfile.pdf')
        """
        s3 = self._get_s3_client()
        
        # If no local path provided, use the filename from S3 path
        if local_file_path is None:
            local_file_path = os.path.basename(s3_file_path)
        
        # Create directory if it doesn't exist
        local_dir = os.path.dirname(local_file_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        
        try:
            # Download the file
            self.stdout.write(f"Downloading {s3_file_path} from bucket '{bucket_name}'...")
            s3.download_file(bucket_name, s3_file_path, local_file_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully downloaded to {local_file_path}"))
            return local_file_path
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading {s3_file_path}: {e}"))
            raise
    
    def download_file_to_memory(self, s3_file_path, bucket_name="sds"):
        """
        Download a file from S3 Contabo to memory (without saving to disk).
        
        Args:
            s3_file_path: The path/key of the file in S3
            bucket_name: The S3 bucket name (default: 'sds')
            
        Returns:
            bytes: The file content as bytes
            
        Example:
            content = self.download_file_to_memory('s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf')
        """
        s3 = self._get_s3_client()
        
        try:
            self.stdout.write(f"Downloading {s3_file_path} to memory...")
            response = s3.get_object(Bucket=bucket_name, Key=s3_file_path)
            content = response['Body'].read()
            self.stdout.write(self.style.SUCCESS(f"Successfully downloaded {len(content)} bytes"))
            return content
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading {s3_file_path}: {e}"))
            raise


def calculate_md5(file_path, chunk_size=8192):
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read (default 8192 bytes)
        
    Returns:
        str: MD5 hash as hexadecimal string
    """
    md5_hash = hashlib.md5()
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def get_md5_from_file_path(file_path: str):
    full_filename = os.path.basename(file_path)
    filename, _ = full_filename.rsplit(".", 1)
    return filename


def extract_first_page_text(pdf_path):
    """
    Extract text from the first page of a PDF file using PyMuPDF.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Text content from the first page
    """
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)
        
        if len(doc) == 0:
            doc.close()
            raise ValueError("PDF has no pages")
        
        # Get the first page (index 0)
        first_page = doc[0]
        
        # Extract text from the first page
        text = first_page.get_text()
        
        # Close the document
        doc.close()
        
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF with PyMuPDF: {str(e)}")


def remove_special_characters(text):
    """
    Remove all special characters from text, keeping only alphanumeric and whitespace.
    Supports international characters (Unicode letters and digits).
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with special characters removed
    """
    # Remove all characters except Unicode letters, digits, and whitespace
    # \w matches Unicode word characters (letters, digits, underscore from any language)
    # We exclude underscore and keep only letters (\p{L} equivalent), digits (\d), and whitespace (\s)
    cleaned_text = re.sub(r'[^\w\s]|_', '', text, flags=re.UNICODE)
    
    # Alternative more explicit pattern that works with all Unicode scripts:
    # cleaned_text = re.sub(r'[^\p{L}\p{N}\s]', '', text)
    # But Python's re doesn't support \p{} so we use \w which includes Unicode letters/digits
    
    # Normalize whitespace (collapse multiple spaces into one)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def generate_md5(text):
    """
    Generate MD5 hash of the given text.
    
    Args:
        text (str): Input text
        
    Returns:
        str: MD5 hash as hexadecimal string
    """
    md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return md5_hash


def process_pdf_to_md5(pdf_path):
    """
    Read first page of PDF, detect language, remove special characters, and generate MD5 hash.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing cleaned text, MD5 hash, and detected language
    """
    # Extract text from first page
    raw_text = extract_first_page_text(pdf_path)
    print(f"Raw text extracted ({len(raw_text)} characters)")
    
    # Detect language
    detected_language = None
    try:
        if raw_text and len(raw_text.strip()) > 0:
            detected_language = detect(raw_text)
            print(f"Detected language: {detected_language}")
        else:
            print("Warning: No text to detect language from")
    except LangDetectException as e:
        print(f"Warning: Could not detect language: {e}")
    except Exception as e:
        print(f"Warning: Error during language detection: {e}")
    
    # Remove special characters
    cleaned_text = remove_special_characters(raw_text)
    print(f"Cleaned text ({len(cleaned_text)} characters)")
    
    # Generate MD5
    md5_hash = generate_md5(cleaned_text)
    print(f"MD5 hash: {md5_hash}")
    
    return {
        'raw_text': raw_text,
        'cleaned_text': cleaned_text,
        'md5_hash': md5_hash,
        'language': detected_language
    }
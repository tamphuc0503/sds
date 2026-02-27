import hashlib
import sys
import os


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


def check_md5(file_path, expected_md5=None):
    """
    Check the MD5 hash of a specified file.
    
    Args:
        file_path: Path to the file
        expected_md5: Optional expected MD5 hash to compare against
        
    Returns:
        bool: True if matches expected_md5 (or if no expected_md5 provided)
    """
    if not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(file_path)
    print(f"File: {file_path}")
    print(f"Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Calculate MD5
    print("Calculating MD5 hash...")
    calculated_md5 = calculate_md5(file_path)
    
    if calculated_md5 is None:
        return False
    
    print(f"MD5: {calculated_md5}")
    
    # Compare with expected MD5 if provided
    if expected_md5:
        expected_md5_clean = expected_md5.strip().lower()
        calculated_md5_clean = calculated_md5.lower()
        
        if calculated_md5_clean == expected_md5_clean:
            print(f"✓ MD5 matches expected value!")
            return True
        else:
            print(f"✗ MD5 does NOT match!")
            print(f"  Expected:   {expected_md5_clean}")
            print(f"  Calculated: {calculated_md5_clean}")
            return False
    
    return True


def main():
    """
    Command line interface for checking MD5 of files.
    
    Usage:
        python check_md5.py <file_path> [expected_md5]
    """
    if len(sys.argv) < 2:
        print("Usage: python check_md5.py <file_path> [expected_md5]")
        print()
        print("Examples:")
        print("  python check_md5.py myfile.pdf")
        print("  python check_md5.py myfile.pdf 0293a0ea54eb69d6b750eab79334288b")
        sys.exit(1)
    
    file_path = sys.argv[1]
    expected_md5 = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_md5(file_path, expected_md5)


if __name__ == "__main__":
    main()

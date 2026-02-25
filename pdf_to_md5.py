import hashlib
import re
from pypdf import PdfReader


def extract_first_page_text(pdf_path):
    """
    Extract text from the first page of a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Text content from the first page
    """
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
        
        first_page = reader.pages[0]
        text = first_page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


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
    Read first page of PDF, remove special characters, and generate MD5 hash.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing cleaned text and MD5 hash
    """
    # Extract text from first page
    raw_text = extract_first_page_text(pdf_path)
    print(f"Raw text extracted ({len(raw_text)} characters)")
    
    # Remove special characters
    cleaned_text = remove_special_characters(raw_text)
    print(f"Cleaned text ({len(cleaned_text)} characters)")
    
    # Generate MD5
    md5_hash = generate_md5(cleaned_text)
    print(f"MD5 hash: {md5_hash}")
    
    return {
        'raw_text': raw_text,
        'cleaned_text': cleaned_text,
        'md5_hash': md5_hash
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md5.py <path_to_pdf>")
        print("\nExample: python pdf_to_md5.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        result = process_pdf_to_md5(pdf_path)
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"\nCleaned Text Preview (first 200 chars):")
        print(result['cleaned_text'][:200] + "..." if len(result['cleaned_text']) > 200 else result['cleaned_text'])
        print(f"\nMD5 Hash: {result['md5_hash']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

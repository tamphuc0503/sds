import os
from pathlib import Path

# Example file path
file_path = "s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf"

# Method 1: Using os.path.splitext()
filename_with_ext = os.path.basename(file_path)
filename, extension = os.path.splitext(filename_with_ext)
print(f"Method 1 (os.path.splitext):")
print(f"  Filename: {filename}")
print(f"  Extension: {extension}")
print()

# Method 2: Using pathlib
path = Path(file_path)
filename2 = path.stem  # filename without extension
extension2 = path.suffix  # extension with dot
print(f"Method 2 (pathlib):")
print(f"  Filename: {filename2}")
print(f"  Extension: {extension2}")
print()

# Method 3: Get full filename and split manually
full_filename = os.path.basename(file_path)
if '.' in full_filename:
    filename3, extension3 = full_filename.rsplit('.', 1)  # rsplit to handle multiple dots
    extension3 = '.' + extension3
else:
    filename3 = full_filename
    extension3 = ''
print(f"Method 3 (manual split):")
print(f"  Filename: {filename3}")
print(f"  Extension: {extension3}")
print()

# Example with file that has multiple dots
file_path2 = "archive.tar.gz"
name, ext = os.path.splitext(file_path2)
print(f"File with multiple dots: {file_path2}")
print(f"  os.path.splitext: name={name}, ext={ext}")
print(f"  pathlib: stem={Path(file_path2).stem}, suffix={Path(file_path2).suffix}")

# Output:
# Method 1 (os.path.splitext):
#   Filename: 0293a0ea54eb69d6b750eab79334288b
#   Extension: .pdf
#
# Method 2 (pathlib):
#   Filename: 0293a0ea54eb69d6b750eab79334288b
#   Extension: .pdf

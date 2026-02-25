import os

# Example file path
file_path = "s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf"

# Method 1: Using os.path.basename()
filename = os.path.basename(file_path)
print(f"Method 1 (os.path.basename): {filename}")

# Method 2: Using split() on the path separator
filename2 = file_path.split('/')[-1]
print(f"Method 2 (split): {filename2}")

# Method 3: Using pathlib (modern Python approach)
from pathlib import Path
filename3 = Path(file_path).name
print(f"Method 3 (pathlib): {filename3}")

# All methods output: 0293a0ea54eb69d6b750eab79334288b.pdf

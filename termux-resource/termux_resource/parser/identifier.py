import os
import subprocess

def identify_image(image_path):
    """
    Identifies the type of an Android image file.
    """
    if not os.path.exists(image_path):
        return "File not found"

    with open(image_path, 'rb') as f:
        magic = f.read(8)

    if magic == b'ANDROID!':
        return "Android boot image"
    elif magic == b'VNDRBOOT':
        return "Android vendor boot image"
    elif magic == b'AVB0':
        return "Android verified boot metadata"
    else:
        try:
            result = subprocess.run(['blkid', '-o', 'value', '-s', 'TYPE', image_path], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Unknown image type"

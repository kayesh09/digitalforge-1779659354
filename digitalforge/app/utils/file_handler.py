"""
Secure file handling utilities.
Validates file types, handles uploads, and manages storage.
"""
import os
import secrets
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_PRODUCT_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = (1920, 1080)
MAX_IMAGE_FILESIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename, file_type='product'):
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'product':
        return ext in ALLOWED_PRODUCT_EXTENSIONS
    elif file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    return False

def secure_unique_filename(original_filename, prefix=''):
    """Generate cryptographically secure unique filename."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    random_part = secrets.token_hex(8)
    safe_name = secure_filename(original_filename.rsplit('.', 1)[0])
    return f"{prefix}{random_part}_{safe_name}.{ext}"

def validate_image_content(file_storage):
    """Validate that file is actually an image by trying to open it with PIL."""
    try:
        file_storage.seek(0)
        with Image.open(file_storage) as img:
            # Verify it's a valid image
            img.verify()
        file_storage.seek(0)
        return True
    except Exception:
        return False

def save_preview_images(image_files, product_slug, app):
    """
    Save and optimize preview images.
    Returns list of saved file paths.
    """
    saved_paths = []
    upload_dir = app.config['UPLOAD_FOLDER_PREVIEWS']

    for img_file in image_files:
        if not img_file or not allowed_file(img_file.filename, 'image'):
            continue

        # Validate actual image content using PIL instead of imghdr
        if not validate_image_content(img_file):
            continue

        # Check file size
        img_file.seek(0, os.SEEK_END)
        size = img_file.tell()
        img_file.seek(0)

        if size > MAX_IMAGE_FILESIZE:
            continue

        # Generate unique filename
        filename = secure_unique_filename(img_file.filename, f"{product_slug}_")
        filepath = os.path.join(upload_dir, filename)

        # Save and optimize
        try:
            with Image.open(img_file) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Resize if too large
                img.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)

                # Save with optimization
                save_kwargs = {'optimize': True, 'quality': 85}
                if img.format == 'PNG':
                    save_kwargs = {'optimize': True}

                img.save(filepath, **save_kwargs)
                saved_paths.append(f"uploads/previews/{filename}")
        except Exception as e:
            app.logger.error(f"Image processing error: {e}")
            continue

    return saved_paths

def validate_zip_content(file_path):
    """
    Validate ZIP file contents for security.
    """
    import zipfile

    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # Check for path traversal attacks
            for name in zf.namelist():
                if name.startswith('/') or '..' in name:
                    return False, f"Invalid path in zip: {name}"

            # Check file sizes (prevent zip bomb)
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > 500 * 1024 * 1024:  # 500MB extracted max
                return False, "Extracted size too large"

            return True, "Valid"
    except zipfile.BadZipFile:
        return False, "Invalid ZIP file"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
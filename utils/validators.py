import os
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from config import MAX_KB_FILES, MAX_KB_FILE_SIZE, ALLOWED_KB_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    return secure_filename(filename or 'document')


def validate_upload_files(files) -> Tuple[bool, Optional[str]]:
    if not files:
        return False, 'No files were provided.'
    if len(files) > MAX_KB_FILES:
        return False, f'You can upload up to {MAX_KB_FILES} files at a time.'
    seen_names = set()
    for file_storage in files:
        if file_storage.filename == '':
            return False, 'One of the selected files is empty.'
        name = file_storage.filename.lower()
        if name in seen_names:
            return False, 'Duplicate file names are not allowed.'
        seen_names.add(name)
        ext = os.path.splitext(name)[1]
        if ext not in ALLOWED_KB_EXTENSIONS:
            return False, f'Unsupported file type: {ext or "unknown"}'
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
        if size > MAX_KB_FILE_SIZE:
            return False, f'File too large: {file_storage.filename}'
    return True, None

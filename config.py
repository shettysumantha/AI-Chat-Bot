import os

MAX_KB_FILES = 3
MAX_KB_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_KB_EXTENSIONS = {
    '.pdf', '.docx', '.txt', '.csv', '.xlsx', '.pptx', '.md', '.json'
}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'kb')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Nexa AI Chatbot

A Flask-based AI assistant with user authentication, profile management, chat flow, and a PostgreSQL-backed Knowledge Base module for document upload and Q&A.

## What is already implemented

- Flask web app with login/register and session-based authentication
- Profile management and photo upload
- Chat interface with basic bot responses
- PostgreSQL database initialization and connection helpers
- Knowledge Base workflow with:
  - conversation creation
  - document upload validation
  - document storage
  - chunk storage
  - chat history persistence
  - conversation status tracking

## Project structure

- [app.py](app.py) – Flask app entry point and routes
- [database/db.py](database/db.py) – PostgreSQL connection and initialization
- [database/tables.sql](database/tables.sql) – database schema for conversations, documents, chunks, and chat messages
- [database/functions.sql](database/functions.sql) – PostgreSQL functions for knowledge-base operations
- [routes/knowledge_base_routes.py](routes/knowledge_base_routes.py) – knowledge-base API routes
- [services/knowledge_service.py](services/knowledge_service.py) – business logic for knowledge-base flow
- [utils/validators.py](utils/validators.py) – file validation for uploads
- [static/](static/) – frontend HTML/CSS/JS files

## Requirements

Python 3.8+ is recommended.

Install dependencies:

```bash
pip install -r requirements.txt
```

## PostgreSQL setup

1. Install PostgreSQL and create a database.
2. Create a database named `MyDatabase` (or update the environment variables below).
3. Make sure the PostgreSQL server is running on `localhost:5432`.

### Environment variables

You can override the default database settings with:

```bash
set PG_HOST=localhost
set PG_PORT=5432
set PG_DATABASE=MyDatabase
set PG_USER=postgres
set PG_PASSWORD=your_password
```

If you use a full connection string, you can also set:

```bash
set DATABASE_URL=postgresql://username:password@localhost:5432/MyDatabase
```

## Run the app

From the project folder:

```bash
python app.py
```

By default, the app now listens on all interfaces for local network and production-style access:

```text
http://0.0.0.0:5000/
```

You can also open it on your machine using:

```text
http://127.0.0.1:5000/
```

### Production / public access settings

Use environment variables if you want to control the host and port:

```bash
set HOST=0.0.0.0
set PORT=5000
set FLASK_DEBUG=0
set OPEN_BROWSER=0
python app.py
```

If the app is running on a server, open it using the server IP:

```text
http://YOUR_SERVER_IP:5000/
```

### Host it in VS Code as a browser app

1. Run the app from the terminal:
   ```bash
   python app.py
   ```
2. In VS Code, open the Ports panel or the Run and Debug view.
3. Make port 5000 visible and click the forwarded URL.
4. The app will open in your browser as a hosted web app.

For cloud hosting, the project is now ready to use a simple web process such as Render, Railway, or similar services.

## Knowledge Base flow

The app supports a document-based knowledge workflow:

1. Create a new conversation
2. Upload documents
3. Submit for processing
4. Chat with the AI using the uploaded documents

All conversation data, uploaded files metadata, document chunks, and chat history are stored in PostgreSQL.

## Notes

- Maximum 3 files per upload
- Maximum file size: 20 MB per file
- Allowed extensions: `.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`, `.pptx`, `.md`, `.json`
- The app currently uses the local Flask development server for running locally

## Future improvements

- richer document embeddings/search
- better AI response generation
- admin dashboard
- export/import knowledge conversations

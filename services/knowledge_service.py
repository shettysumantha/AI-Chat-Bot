import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any

from database.db import get_connection
from config import UPLOAD_FOLDER
from services.document_parser import DocumentParser


class KnowledgeService:
    def __init__(self):
        self.parser = DocumentParser()

    def _ensure_user(self, user_id):
        if not user_id:
            raise ValueError('Authentication required')

    def create_conversation(self, user_id: int, title: str) -> int:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_get_conversation_by_title(%s, %s)", (user_id, title))
        existing = cur.fetchone()
        if existing and existing[0] is not None:
            raise ValueError('A conversation with that name already exists')
        cur.execute(
            "SELECT fn_create_kb_conversation(%s, %s) AS conversation_id",
            (user_id, title),
        )
        conversation_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return conversation_id

    def save_document(self, user_id: int, conversation_id: int, file_storage, stored_path: str) -> Dict[str, Any]:
        self._ensure_user(user_id)
        filename = file_storage.filename
        file_size = os.path.getsize(stored_path)
        file_type = os.path.splitext(filename)[1].lower()
        checksum = hashlib.sha256(open(stored_path, 'rb').read()).hexdigest()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT fn_save_uploaded_document(%s, %s, %s, %s, %s, %s, %s) AS document_id",
            (conversation_id, user_id, filename, stored_path, file_size, file_type, checksum),
        )
        document_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {
            'id': document_id,
            'file_name': filename,
            'file_size': file_size,
            'file_type': file_type,
            'file_path': stored_path,
            'status': 'uploaded',
        }

    def save_chunk(self, document_id: int, chunk_index: int, chunk_text: str) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT fn_save_document_chunk(%s, %s, %s)",
            (document_id, chunk_index, chunk_text),
        )
        conn.commit()
        cur.close()
        conn.close()

    def index_document(self, user_id: int, conversation_id: int, document_id: int, file_path: str, file_type: str) -> None:
        text = self.parser.extract_text(file_path, file_type)
        chunks = self.parser.split_text(text)
        for index, chunk in enumerate(chunks):
            self.save_chunk(document_id, index, chunk)

    def get_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_get_user_conversations(%s)", (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                'id': row[0],
                'title': row[1],
                'status': row[2],
                'created_at': row[3],
                'updated_at': row[4],
            }
            for row in rows
        ]

    def get_conversation(self, user_id: int, conversation_id: int) -> Dict[str, Any]:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, status, created_at, updated_at FROM kb_conversations WHERE user_id=%s AND id=%s", (user_id, conversation_id))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {}
        return {'id': row[0], 'title': row[1], 'status': row[2], 'created_at': row[3], 'updated_at': row[4]}

    def get_conversation_documents(self, user_id: int, conversation_id: int) -> List[Dict[str, Any]]:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_get_conversation_documents(%s, %s)", (user_id, conversation_id))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                'id': row[0],
                'file_name': row[1],
                'file_path': row[2],
                'file_size': row[3],
                'file_type': row[4],
                'status': row[5],
                'uploaded_at': row[6],
            }
            for row in rows
        ]

    def get_chat_history(self, user_id: int, conversation_id: int) -> List[Dict[str, Any]]:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_get_chat_history(%s, %s)", (user_id, conversation_id))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                'id': row[0],
                'role': row[1],
                'message': row[2],
                'created_at': row[3],
            }
            for row in rows
        ]

    def save_chat_message(self, user_id: int, conversation_id: int, role: str, message: str) -> None:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_save_chat_message(%s, %s, %s, %s)", (conversation_id, user_id, role, message))
        conn.commit()
        cur.close()
        conn.close()

    def delete_document(self, user_id: int, document_id: int) -> bool:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_delete_document(%s, %s)", (user_id, document_id))
        deleted = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return bool(deleted)

    def delete_conversation(self, user_id: int, conversation_id: int) -> bool:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_delete_conversation(%s, %s)", (user_id, conversation_id))
        deleted = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return bool(deleted)

    def update_conversation_title(self, user_id: int, conversation_id: int, title: str) -> None:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_update_conversation_title(%s, %s, %s)", (user_id, conversation_id, title))
        conn.commit()
        cur.close()
        conn.close()

    def set_conversation_status(self, user_id: int, conversation_id: int, status: str) -> None:
        self._ensure_user(user_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT fn_update_conversation_status(%s, %s, %s)", (user_id, conversation_id, status))
        conn.commit()
        cur.close()
        conn.close()

    def answer_question(self, user_id: int, conversation_id: int, question: str) -> str:
        self._ensure_user(user_id)
        documents = self.get_conversation_documents(user_id, conversation_id)
        if not documents:
            return "I couldn't find that information in your uploaded documents."
        chunks = []
        conn = get_connection()
        cur = conn.cursor()
        for document in documents:
            cur.execute("SELECT chunk_text FROM kb_document_chunks WHERE document_id=%s ORDER BY chunk_index", (document['id'],))
            rows = cur.fetchall()
            for row in rows:
                chunks.append(row[0])
        cur.close()
        conn.close()
        relevant = []
        if chunks:
            lower_question = question.lower()
            for chunk in chunks:
                if lower_question in chunk.lower() or len(set(lower_question.split()) & set(chunk.lower().split())) >= 2:
                    relevant.append(chunk)
            if not relevant:
                relevant = chunks[:3]
        context = '\n'.join(relevant[:5])
        if not context:
            return "I couldn't find that information in your uploaded documents."
        answer = self._build_response(question, context)
        self.save_chat_message(user_id, conversation_id, 'user', question)
        self.save_chat_message(user_id, conversation_id, 'assistant', answer)
        return answer

    def _build_response(self, question: str, context: str) -> str:
        if not context:
            return "I couldn't find that information in your uploaded documents."
        prompt = (
            "You are a careful document assistant. Answer the user's question using ONLY the supplied context. "
            "If the answer is not present in the context, say exactly: I couldn't find that information in your uploaded documents.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )
        return prompt

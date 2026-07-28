import os
from flask import Blueprint, request, jsonify, session

from config import MAX_KB_FILES, UPLOAD_FOLDER
from services.knowledge_service import KnowledgeService
from utils.validators import validate_upload_files, sanitize_filename

knowledge_bp = Blueprint('knowledge_bp', __name__)
knowledge_service = KnowledgeService()


@knowledge_bp.route('/api/kb/conversation', methods=['POST'])
def create_conversation():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Conversation name is required'}), 400
    if len(title) < 3:
        return jsonify({'error': 'Conversation name must be at least 3 characters'}), 400
    if len(title) > 100:
        return jsonify({'error': 'Conversation name cannot exceed 100 characters'}), 400
    try:
        conversation_id = knowledge_service.create_conversation(user_id, title)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    return jsonify({'ok': True, 'conversation': {'id': conversation_id, 'title': title, 'status': 'waiting_for_documents'}})


@knowledge_bp.route('/api/kb/upload', methods=['POST'])
def upload_documents():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if 'files' not in request.files:
        return jsonify({'error': 'No files were provided'}), 400
    files = request.files.getlist('files')
    valid, error = validate_upload_files(files)
    if not valid:
        return jsonify({'error': error}), 400
    conversation_id = request.form.get('conversation_id', type=int)
    if not conversation_id:
        return jsonify({'error': 'Conversation is required'}), 400
    conversation = knowledge_service.get_conversation(user_id, conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    if conversation['status'] == 'completed':
        return jsonify({'error': 'Documents have already been submitted for this conversation'}), 409
    knowledge_service.set_conversation_status(user_id, conversation_id, 'processing')
    uploaded = []
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for file_storage in files:
        original_name = sanitize_filename(file_storage.filename)
        save_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_{conversation_id}_{original_name}")
        file_storage.save(save_path)
        document = knowledge_service.save_document(user_id, conversation_id, file_storage, save_path)
        knowledge_service.index_document(user_id, conversation_id, document['id'], save_path, document['file_type'])
        uploaded.append(document)
    knowledge_service.set_conversation_status(user_id, conversation_id, 'completed')
    knowledge_service.save_chat_message(
        user_id,
        conversation_id,
        'assistant',
        'Your documents have been processed successfully.\n\nYou can now ask questions based on the uploaded documents.',
    )
    return jsonify({'ok': True, 'conversation_id': conversation_id, 'documents': uploaded})


@knowledge_bp.route('/api/kb/conversations', methods=['GET'])
def get_conversations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'conversations': knowledge_service.get_conversations(user_id)})


@knowledge_bp.route('/api/kb/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    documents = knowledge_service.get_conversation_documents(user_id, conversation_id)
    history = knowledge_service.get_chat_history(user_id, conversation_id)
    conversation = knowledge_service.get_conversation(user_id, conversation_id)
    return jsonify({'conversation_id': conversation_id, 'conversation': conversation, 'documents': documents, 'history': history})


@knowledge_bp.route('/api/kb/chat', methods=['POST'])
def chat_with_kb():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    conversation_id = data.get('conversation_id')
    question = (data.get('message') or '').strip()
    if not conversation_id or not question:
        return jsonify({'error': 'Missing conversation or question'}), 400
    answer = knowledge_service.answer_question(user_id, conversation_id, question)
    return jsonify({'answer': answer})


@knowledge_bp.route('/api/kb/messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    history = knowledge_service.get_chat_history(user_id, conversation_id)
    return jsonify({'messages': history})


@knowledge_bp.route('/api/kb/documents/<int:conversation_id>', methods=['GET'])
def get_documents(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'documents': knowledge_service.get_conversation_documents(user_id, conversation_id)})


@knowledge_bp.route('/api/kb/document/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    deleted = knowledge_service.delete_document(user_id, document_id)
    if not deleted:
        return jsonify({'error': 'Document not found'}), 404
    return jsonify({'ok': True})


@knowledge_bp.route('/api/kb/conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    deleted = knowledge_service.delete_conversation(user_id, conversation_id)
    if not deleted:
        return jsonify({'error': 'Conversation not found'}), 404
    return jsonify({'ok': True})

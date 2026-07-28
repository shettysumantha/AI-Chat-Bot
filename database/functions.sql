CREATE OR REPLACE FUNCTION fn_create_kb_conversation(p_user_id BIGINT, p_title TEXT)
RETURNS BIGINT AS $$
DECLARE v_id BIGINT;
BEGIN
    INSERT INTO kb_conversations(user_id, title, status, created_at, updated_at)
    VALUES (p_user_id, COALESCE(p_title, 'Knowledge Base Conversation'), 'waiting_for_documents', NOW(), NOW())
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_conversation_by_title(p_user_id BIGINT, p_title TEXT)
RETURNS TABLE(id BIGINT, title TEXT, status TEXT, created_at TIMESTAMP, updated_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT kc.id, kc.title, kc.status, kc.created_at, kc.updated_at FROM kb_conversations kc WHERE kc.user_id = p_user_id AND LOWER(kc.title) = LOWER(p_title);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_save_uploaded_document(p_conversation_id BIGINT, p_user_id BIGINT, p_file_name TEXT, p_file_path TEXT, p_file_size BIGINT, p_file_type TEXT, p_checksum TEXT)
RETURNS BIGINT AS $$
DECLARE v_id BIGINT;
BEGIN
    INSERT INTO kb_documents(conversation_id, user_id, file_name, file_path, file_size, file_type, status, uploaded_at, checksum)
    VALUES (p_conversation_id, p_user_id, p_file_name, p_file_path, p_file_size, p_file_type, 'uploaded', NOW(), p_checksum)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_save_document_chunk(p_document_id BIGINT, p_chunk_index INT, p_chunk_text TEXT, p_embedding TEXT DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO kb_document_chunks(document_id, chunk_index, chunk_text, embedding, created_at) VALUES (p_document_id, p_chunk_index, p_chunk_text, p_embedding, NOW());
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_mark_conversation_ready(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE kb_conversations SET status = 'ready', updated_at = NOW() WHERE id = p_conversation_id AND user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_document_chunks(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS TABLE(document_id BIGINT, chunk_index INT, chunk_text TEXT, embedding TEXT) AS $$
BEGIN
    RETURN QUERY SELECT dc.document_id, dc.chunk_index, dc.chunk_text, dc.embedding FROM kb_document_chunks dc JOIN kb_documents d ON d.id = dc.document_id WHERE d.user_id = p_user_id AND d.conversation_id = p_conversation_id ORDER BY dc.document_id, dc.chunk_index;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_user_conversations(p_user_id BIGINT)
RETURNS TABLE(id BIGINT, title TEXT, status TEXT, created_at TIMESTAMP, updated_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT kc.id, kc.title, kc.status, kc.created_at, kc.updated_at FROM kb_conversations kc WHERE kc.user_id = p_user_id ORDER BY kc.updated_at DESC, kc.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_recent_conversations(p_user_id BIGINT)
RETURNS TABLE(id BIGINT, title TEXT, status TEXT, created_at TIMESTAMP, updated_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT kc.id, kc.title, kc.status, kc.created_at, kc.updated_at FROM kb_conversations kc WHERE kc.user_id = p_user_id AND kc.status IN ('ready', 'completed') ORDER BY kc.updated_at DESC, kc.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_conversation(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS TABLE(id BIGINT, title TEXT, status TEXT, created_at TIMESTAMP, updated_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT kc.id, kc.title, kc.status, kc.created_at, kc.updated_at FROM kb_conversations kc WHERE kc.user_id = p_user_id AND kc.id = p_conversation_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_conversation_documents(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS TABLE(id BIGINT, file_name TEXT, file_path TEXT, file_size BIGINT, file_type TEXT, status TEXT, uploaded_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT kd.id, kd.file_name, kd.file_path, kd.file_size, kd.file_type, kd.status, kd.uploaded_at FROM kb_documents kd WHERE kd.user_id = p_user_id AND kd.conversation_id = p_conversation_id ORDER BY kd.uploaded_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_documents_by_conversation(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS TABLE(id BIGINT, file_name TEXT, file_path TEXT, file_size BIGINT, file_type TEXT, status TEXT, uploaded_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT * FROM fn_get_conversation_documents(p_user_id, p_conversation_id);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_get_chat_history(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS TABLE(id BIGINT, role TEXT, message TEXT, created_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY SELECT km.id, km.role, km.message, km.created_at FROM kb_chat_messages km WHERE km.user_id = p_user_id AND km.conversation_id = p_conversation_id ORDER BY km.created_at ASC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_save_chat_message(p_conversation_id BIGINT, p_user_id BIGINT, p_role TEXT, p_message TEXT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO kb_chat_messages(conversation_id, user_id, role, message, created_at) VALUES (p_conversation_id, p_user_id, p_role, p_message, NOW());
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_delete_document(p_user_id BIGINT, p_document_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE v_deleted BOOLEAN := FALSE;
BEGIN
    DELETE FROM kb_documents WHERE id = p_document_id AND user_id = p_user_id;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted > 0;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_delete_conversation(p_user_id BIGINT, p_conversation_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE v_deleted BOOLEAN := FALSE;
BEGIN
    DELETE FROM kb_conversations WHERE id = p_conversation_id AND user_id = p_user_id;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted > 0;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_update_conversation_title(p_user_id BIGINT, p_conversation_id BIGINT, p_title TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE kb_conversations SET title = p_title, updated_at = NOW() WHERE id = p_conversation_id AND user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_update_conversation_status(p_user_id BIGINT, p_conversation_id BIGINT, p_status TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE kb_conversations SET status = p_status, updated_at = NOW() WHERE id = p_conversation_id AND user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

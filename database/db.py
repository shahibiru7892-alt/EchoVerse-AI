import sqlite3
from pathlib import Path
import secrets


# ==========================================
# DATABASE LOCATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "echoverse.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_database():

    connection = get_connection()

    try:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
            )
        """)

        # ==================================
        # DATABASE MIGRATION FOR IMAGES
        # ==================================

        columns = connection.execute(
            "PRAGMA table_info(messages)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "image_data" not in column_names:

            connection.execute("""
                ALTER TABLE messages
                ADD COLUMN image_data TEXT
            """)

        if "image_mime_type" not in column_names:

            connection.execute("""
                ALTER TABLE messages
                ADD COLUMN image_mime_type TEXT
            """)

        # ==================================
        # FEEDBACK TABLE
        # ==================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                message_id INTEGER,
                rating TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==================================
        # SHARED CONVERSATIONS TABLE
        # ==================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS shared_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL UNIQUE,
                share_token TEXT NOT NULL UNIQUE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
            )
        """)

        connection.commit()

    finally:
        connection.close()


# ==========================================
# CREATE CONVERSATION
# ==========================================

def create_conversation():

    connection = get_connection()

    try:

        cursor = connection.execute(
            "INSERT INTO conversations DEFAULT VALUES"
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ==========================================
# GET CONVERSATIONS
# ==========================================

def get_conversations():

    connection = get_connection()

    try:

        cursor = connection.execute("""
            SELECT id, title, created_at
            FROM conversations
            ORDER BY id DESC
        """)

        return cursor.fetchall()

    finally:
        connection.close()


# ==========================================
# SAVE MESSAGE
# ==========================================

def save_message(
    conversation_id,
    role,
    content,
    image_data=None,
    image_mime_type=None
):

    connection = get_connection()

    try:

        connection.execute("""
            INSERT INTO messages (
                conversation_id,
                role,
                content,
                image_data,
                image_mime_type
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            conversation_id,
            role,
            content,
            image_data,
            image_mime_type
        ))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# GET MESSAGES
# ==========================================

def get_messages(conversation_id):

    connection = get_connection()

    try:

        cursor = connection.execute("""
            SELECT
                role,
                content,
                image_data,
                image_mime_type
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
        """, (conversation_id,))

        return [
            {
                "role": row[0],
                "content": row[1],
                "image_data": row[2],
                "image_mime_type": row[3]
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# GET MESSAGES WITH TIMESTAMPS
# ==========================================

def get_messages_with_timestamps(conversation_id):

    connection = get_connection()

    try:

        cursor = connection.execute("""
            SELECT
                role,
                content,
                created_at,
                image_data,
                image_mime_type
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
        """, (conversation_id,))

        return [
            {
                "role": row[0],
                "content": row[1],
                "created_at": row[2],
                "image_data": row[3],
                "image_mime_type": row[4]
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# ==========================================
# CLEAR MESSAGES
# ==========================================

def clear_messages(conversation_id):

    connection = get_connection()

    try:

        connection.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# UPDATE CONVERSATION TITLE
# ==========================================

def update_conversation_title(conversation_id, title):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE conversations
            SET title = ?
            WHERE id = ?
        """, (title, conversation_id))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# DELETE CONVERSATION
# ==========================================

def delete_conversation(conversation_id):

    connection = get_connection()

    try:

        connection.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.execute("""
            DELETE FROM feedback
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.execute("""
            DELETE FROM shared_conversations
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.execute("""
            DELETE FROM conversations
            WHERE id = ?
        """, (conversation_id,))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# RENAME CONVERSATION
# ==========================================

def rename_conversation(conversation_id, new_title):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE conversations
            SET title = ?
            WHERE id = ?
        """, (new_title, conversation_id))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# SAVE FEEDBACK
# ==========================================

def save_feedback(conversation_id, message_id, rating):

    connection = get_connection()

    try:

        existing = connection.execute("""
            SELECT id
            FROM feedback
            WHERE conversation_id = ?
            AND message_id = ?
        """, (conversation_id, message_id)).fetchone()

        if existing:
            return False

        connection.execute("""
            INSERT INTO feedback (
                conversation_id,
                message_id,
                rating
            )
            VALUES (?, ?, ?)
        """, (conversation_id, message_id, rating))

        connection.commit()

        return True

    finally:
        connection.close()


# ==========================================
# DELETE LAST EXCHANGE
# ==========================================

def delete_last_exchange(conversation_id):

    connection = get_connection()

    try:

        connection.execute("""
            DELETE FROM messages
            WHERE id IN (
                SELECT id
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT 2
            )
        """, (conversation_id,))

        connection.commit()

    finally:
        connection.close()


# ==========================================
# CHATBOT STATISTICS
# ==========================================

def get_statistics():

    connection = get_connection()

    try:

        total_conversations = connection.execute(
            "SELECT COUNT(*) FROM conversations"
        ).fetchone()[0]

        total_messages = connection.execute(
            "SELECT COUNT(*) FROM messages"
        ).fetchone()[0]

        total_ai_responses = connection.execute(
            "SELECT COUNT(*) FROM messages WHERE role = 'assistant'"
        ).fetchone()[0]

        helpful_feedback = connection.execute(
            "SELECT COUNT(*) FROM feedback WHERE rating = 'like'"
        ).fetchone()[0]

        negative_feedback = connection.execute(
            "SELECT COUNT(*) FROM feedback WHERE rating = 'dislike'"
        ).fetchone()[0]

        return {
            "conversations": total_conversations,
            "messages": total_messages,
            "ai_responses": total_ai_responses,
            "helpful": helpful_feedback,
            "not_helpful": negative_feedback
        }

    finally:
        connection.close()


# ==========================================
# CREATE SHARE LINK
# ==========================================

def create_share_link(conversation_id):

    connection = get_connection()

    try:

        existing = connection.execute("""
            SELECT share_token
            FROM shared_conversations
            WHERE conversation_id = ?
        """, (conversation_id,)).fetchone()

        if existing:

            connection.execute("""
                UPDATE shared_conversations
                SET is_active = 1
                WHERE conversation_id = ?
            """, (conversation_id,))

            connection.commit()

            return existing[0]

        share_token = secrets.token_urlsafe(32)

        connection.execute("""
            INSERT INTO shared_conversations (
                conversation_id,
                share_token
            )
            VALUES (?, ?)
        """, (conversation_id, share_token))

        connection.commit()

        return share_token

    finally:
        connection.close()


# ==========================================
# GET SHARED CONVERSATION
# ==========================================

def get_shared_conversation(share_token):

    connection = get_connection()

    try:

        conversation = connection.execute("""
            SELECT c.title
            FROM shared_conversations s
            JOIN conversations c
            ON s.conversation_id = c.id
            WHERE s.share_token = ?
            AND s.is_active = 1
        """, (share_token,)).fetchone()

        if not conversation:
            return None

        messages = connection.execute("""
            SELECT
                role,
                content,
                created_at,
                image_data,
                image_mime_type
            FROM messages
            WHERE conversation_id = (
                SELECT conversation_id
                FROM shared_conversations
                WHERE share_token = ?
                AND is_active = 1
            )
            ORDER BY id
        """, (share_token,)).fetchall()

        return {
            "title": conversation[0],
            "messages": [
                {
                    "role": row[0],
                    "content": row[1],
                    "created_at": row[2],
                    "image_data": row[3],
                    "image_mime_type": row[4]
                }
                for row in messages
            ]
        }

    finally:
        connection.close()


# ==========================================
# DISABLE SHARE LINK
# ==========================================

def disable_share_link(conversation_id):

    connection = get_connection()

    try:

        connection.execute("""
            UPDATE shared_conversations
            SET is_active = 0
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.commit()

    finally:
        connection.close()
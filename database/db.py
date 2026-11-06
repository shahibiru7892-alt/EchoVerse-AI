import sqlite3
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "echoverse.db"


# Connect to database
def get_connection():

    return sqlite3.connect(DB_PATH)


# Create database tables
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

        columns = connection.execute(
            "PRAGMA table_info(conversations)"
        ).fetchall()

        column_names = [column[1] for column in columns]

        if "title" not in column_names:
            connection.execute(
            "ALTER TABLE conversations ADD COLUMN title TEXT DEFAULT 'New Chat'"
    )
        
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

        # Create feedback table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                message_id INTEGER,
                rating TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    finally:
        connection.close()


# Create new conversation
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

# Get all conversations
def get_conversations():

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()

    finally:
        connection.close()
        
# Save message
def save_message(conversation_id, role, content):

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content)
        )

        connection.commit()

    finally:
        connection.close()


# Get conversation history
def get_messages(conversation_id):

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
            """,
            (conversation_id,)
        )

        return [
            {"role": row[0], "content": row[1]}
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# Clear conversation messages
def clear_messages(conversation_id):

    connection = get_connection()

    try:
        connection.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )

        connection.commit()

    finally:
        connection.close()

# Update conversation title
def update_conversation_title(conversation_id, title):

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ?
            """,
            (title, conversation_id)
        )

        connection.commit()

    finally:
        connection.close()

# Delete a conversation
def delete_conversation(conversation_id):

    connection = get_connection()

    try:
        # Delete messages first
        connection.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )

        # Delete conversation
        connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )

        connection.commit()

    finally:
        connection.close()

# Rename conversation
def rename_conversation(conversation_id, new_title):

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ?
            """,
            (new_title, conversation_id)
        )

        connection.commit()

    finally:
        connection.close()

# Get messages with timestamps
def get_messages_with_timestamps(conversation_id):

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
            """,
            (conversation_id,)
        )

        return [
            {
                "role": row[0],
                "content": row[1],
                "created_at": row[2]
            }
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()

# Save user feedback
def save_feedback(conversation_id, message_id, rating):

    connection = sqlite3.connect(DB_PATH)

    existing = connection.execute(
        """
        SELECT id FROM feedback
        WHERE conversation_id = ? AND message_id = ?
        """,
        (conversation_id, message_id)
    ).fetchone()

    if existing:
        connection.close()
        return False

    connection.execute(
        """
        INSERT INTO feedback
        (conversation_id, message_id, rating)
        VALUES (?, ?, ?)
        """,
        (conversation_id, message_id, rating)
    )

    connection.commit()
    connection.close()

    return True

# Delete the latest user question and assistant response
def delete_last_exchange(conversation_id):

    connection = sqlite3.connect(DB_PATH)

    connection.execute(
        """
        DELETE FROM messages
        WHERE id IN (
            SELECT id FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT 2
        )
        """,
        (conversation_id,)
    )

    connection.commit()
    connection.close()

# Get chatbot statistics
def get_statistics():

    connection = sqlite3.connect(DB_PATH)

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

    connection.close()

    return {
        "conversations": total_conversations,
        "messages": total_messages,
        "ai_responses": total_ai_responses,
        "helpful": helpful_feedback,
        "not_helpful": negative_feedback
    }
import streamlit as st
from pathlib import Path
from datetime import datetime

from chatbot import (
    generate_response,
    generate_response_stream,
    clear_memory
)
from database.db import (
    initialize_database,
    create_conversation,
    get_messages,
    get_conversations,
    update_conversation_title,
    delete_conversation,
    rename_conversation,
    get_messages_with_timestamps,
    save_feedback,
    delete_last_exchange,
    get_statistics
)
from pdf_export import generate_chat_pdf

# Page configuration
st.set_page_config(
    page_title="EchoVerse AI",
    page_icon="🎭",
    layout="wide"
)


# Load CSS
css_path = Path(__file__).parent / "assets" / "style.css"

with open(css_path, encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )


# Initialize database
initialize_database()


# Create conversation
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = create_conversation()

# Sidebar
with st.sidebar:
    # Statistics Dashboard
    with st.sidebar.expander("📊 Chatbot Statistics"):

        stats = get_statistics()

        st.metric("Total Conversations", stats["conversations"])

        st.metric("Total Messages", stats["messages"])

        st.metric("AI Responses", stats["ai_responses"])

        st.metric("👍 Helpful", stats["helpful"])

        st.metric("👎 Not Helpful", stats["not_helpful"])

    st.title("🎭 EchoVerse AI")

    st.caption("Your AI Entertainment Companion")

    st.divider()

    # New Chat
    if st.button("➕ New Chat", use_container_width=True):

        st.session_state.conversation_id = create_conversation()

        st.rerun()

    # Clear current chat
    if st.button("🗑️ Clear Current Chat", use_container_width=True):

        st.session_state.confirm_clear = True

        st.rerun()


    # Clear chat confirmation
    if st.session_state.get("confirm_clear", False):

        st.warning("Are you sure you want to clear this conversation?")

        col1, col2 = st.columns(2)

        with col1:

            if st.button("Yes, Clear", key="confirm_clear_chat"):

                clear_memory(st.session_state.conversation_id)

                st.session_state.confirm_clear = False

                st.rerun()

        with col2:

            if st.button("Cancel", key="cancel_clear_chat"):

                st.session_state.confirm_clear = False

                st.rerun()

    st.divider()

# Conversation History
st.subheader("💬 Chat History")

conversations = get_conversations()

# Search conversations
search_query = st.text_input(
    "🔍 Search chats",
    placeholder="Search conversations..."
)

if search_query:
    conversations = [
        chat for chat in conversations
        if search_query.lower() in chat[1].lower()
    ]

for conversation in conversations:

    conversation_id = conversation[0]
    label = conversation[1]

    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:

        if st.button(
            label,
            key=f"chat_{conversation_id}",
            use_container_width=True
        ):

            st.session_state.conversation_id = conversation_id
            st.rerun()

    with col2:

        if st.button("✏️", key=f"rename_{conversation_id}"):

            st.session_state.rename_chat_id = conversation_id
            st.rerun()

    with col3:

        if st.button("🗑️", key=f"delete_{conversation_id}"):

            delete_conversation(conversation_id)

            if st.session_state.conversation_id == conversation_id:
                st.session_state.conversation_id = create_conversation()

            st.rerun()


# Rename conversation form
if "rename_chat_id" in st.session_state:

    st.write("Rename Conversation")

    new_title = st.text_input(
        "Enter new title",
        key="new_conversation_title"
    )

    if st.button("Save Title"):

        if new_title.strip():

            rename_conversation(
                st.session_state.rename_chat_id,
                new_title.strip()
            )

            del st.session_state.rename_chat_id

            st.rerun()

    if st.button("Cancel Rename"):

        del st.session_state.rename_chat_id

        st.rerun()

    st.divider()

    st.caption("Powered by Groq AI")

# Main interface
st.title("🎭 EchoVerse AI")

st.markdown(
    "Your universe of gaming, anime, movies and creativity."
)

st.divider()


# Get conversation history
messages = get_messages_with_timestamps(st.session_state.conversation_id)


# Welcome screen
if not messages:

    st.markdown(
        "<h2 style='text-align:center;'>Welcome to EchoVerse AI 👋</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;'>What would you like to explore today?</p>",
        unsafe_allow_html=True
    )


# Display previous messages
for index, message in enumerate(messages):

    with st.chat_message(message["role"]):

        # Display messages
        if message["role"] == "assistant":

            st.code(
              message["content"],
             language=None
            )

        else:

            st.markdown(message["content"])

    # Display message timestamp
    if message.get("created_at"):
        st.caption(f"🕒 {message['created_at']}")

    # Feedback buttons for AI responses
    if message["role"] == "assistant":

        col1, col2 = st.columns([1, 1])

        with col1:

            if st.button("👍 Helpful", key=f"like_{index}"):

                saved = save_feedback(
                    st.session_state.conversation_id,
                    index,
                    "like"
                )

                if saved:
                    st.success("Thanks for your feedback!")
                else:
                    st.warning("You have already rated this response.")

        with col2:

            if st.button("👎 Not Helpful", key=f"dislike_{index}"):

                saved = save_feedback(
                    st.session_state.conversation_id,
                    index,
                    "dislike"
                )

                if saved:
                    st.success("Thanks for your feedback!")
                else:
                    st.warning("You have already rated this response.")
    
    # Regenerate latest AI response
    if message["role"] == "assistant" and index == len(messages) - 1:

        if st.button("🔄 Regenerate", key=f"regenerate_{index}"):

            last_user_message = next(
                (
                    msg["content"]
                    for msg in reversed(messages[:index])
                    if msg["role"] == "user"
                ),
                None
            )

            if last_user_message:

                st.session_state.regenerate_message = last_user_message

                delete_last_exchange(
                    st.session_state.conversation_id
                )

                st.rerun()

# Export conversation
if messages:

    export_text = ""

    for message in messages:

        role = message["role"].capitalize()

        export_text += f"{role}:\n"
        export_text += message["content"] + "\n"

        if message["created_at"]:
            export_text += f"Time: {message['created_at']}\n"

        export_text += "\n" + "-" * 40 + "\n\n"

    # Download TXT
    st.download_button(
        label="📥 Download Chat",
        data=export_text,
        file_name="echoverse_chat.txt",
        mime="text/plain",
        use_container_width=True
    )

    # Generate PDF
    pdf_file = generate_chat_pdf(
        messages,
        next(
            (
                chat[1]
                for chat in get_conversations()
                if chat[0] == st.session_state.conversation_id
            ),
            "EchoVerse Conversation"
        )
    )

    # Download PDF
    with open(pdf_file, "rb") as file:

        st.download_button(
            label="📄 Download Chat as PDF",
            data=file,
            file_name="echoverse_chat.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Chat input
user_input = st.chat_input("Message EchoVerse AI...")

if user_input:

    # Generate title from the first message
    if not messages:

        title = " ".join(user_input.strip().split()[:5])

        if len(title) > 35:
            title = title[:32] + "..."

        update_conversation_title(
            st.session_state.conversation_id,
            title
        )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        with st.spinner("🎭 EchoVerse AI is thinking..."):

            response = st.write_stream(
                generate_response_stream(
                    user_input,
                    st.session_state.conversation_id
                )
            )
    st.rerun()

# Handle regenerated response
if "regenerate_message" in st.session_state:

    user_message = st.session_state.pop("regenerate_message")

    # Display original user question
    with st.chat_message("user"):
        st.markdown(user_message)

    # Generate a fresh AI response
    with st.chat_message("assistant"):

        with st.spinner("🎭 EchoVerse AI is thinking..."):

           response = st.write_stream(
                generate_response_stream(
                  user_message,
                   st.session_state.conversation_id
             )
         )
    st.rerun()
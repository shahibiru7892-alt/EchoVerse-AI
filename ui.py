import streamlit as st
import textwrap
import json

from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from chatbot import (
    generate_response,
    generate_response_stream,
    clear_memory
)

from vision import analyze_image

from personality import get_available_personalities

from database.db import (
    initialize_database,
    create_conversation,
    get_messages,
    get_conversations,
    update_conversation_title,
    delete_conversation,
    rename_conversation,
    get_messages_with_timestamps,
    delete_last_exchange,
    get_statistics,
    create_share_link,
    get_shared_conversation,
    disable_share_link
)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="EchoVerse AI",
    page_icon="🤖",
    layout="wide"
)


# ==========================================
# LOAD CSS
# ==========================================

css_path = Path(__file__).parent / "assets" / "style.css"

with open(css_path, encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )


# ==========================================
# CHAT INPUT CALLBACK
# ==========================================

def submit_chat_message():
    """
    Called when the user presses Enter
    inside the chat input.
    """
    st.session_state.send_chat_message_requested = True


# ==========================================
# INITIALIZE DATABASE
# ==========================================

initialize_database()


# ==========================================
# INPUT SESSION STATE
# ==========================================

if "image_uploader_key" not in st.session_state:
    st.session_state.image_uploader_key = 0

if "chat_message_input" not in st.session_state:
    st.session_state.chat_message_input = ""

if "send_chat_message_requested" not in st.session_state:
    st.session_state.send_chat_message_requested = False

if st.session_state.get("clear_chat_input", False):

    st.session_state.chat_message_input = ""

    # Reset image uploader safely
    st.session_state.image_uploader_key += 1

    st.session_state.clear_chat_input = False


# ==========================================
# CREATE CONVERSATION
# ==========================================

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = create_conversation()


# ==========================================
# SHARED CONVERSATION
# ==========================================

share_token = st.query_params.get("share")

if share_token:

    shared_chat = get_shared_conversation(share_token)

    if not shared_chat:
        st.error("This sharing link is invalid or has been disabled.")
        st.stop()

    st.title("🤖 EchoVerse AI")
    st.subheader(shared_chat["title"])

    st.info("👁️ You are viewing a shared conversation. This is read-only.")

    for message in shared_chat["messages"]:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        if message.get("created_at"):
            st.caption(message["created_at"])

    st.stop()


# ==========================================
# PREMIUM SIDEBAR
# ==========================================

with st.sidebar:

    with st.expander("📊 Chatbot Statistics"):

        stats = get_statistics()

        st.metric("Total Conversations", stats["conversations"])
        st.metric("Total Messages", stats["messages"])
        st.metric("AI Responses", stats["ai_responses"])

    st.markdown(textwrap.dedent("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">🌌</div>
        <h2>EchoVerse AI</h2>
        <p>Your AI Entertainment Universe</p>
        <div class="sidebar-badge">
            ✨ Powered by Groq AI
        </div>
    </div>
    """), unsafe_allow_html=True)

    st.divider()

    st.subheader("👾 AI Personality")

    personality_options = get_available_personalities()

    selected_personality = st.selectbox(
        "Choose how EchoVerse AI behaves:",
        personality_options,
        key="selected_personality",
        index=0
    )

    st.divider()

    # NEW CHAT

    if st.button("✨ New Chat", use_container_width=True):

        st.session_state.conversation_id = create_conversation()

        st.session_state.focus_chat_input = True
        st.session_state.clear_chat_input = True

        st.rerun()

    # CLEAR CURRENT CHAT

    if st.button("🗑️ Clear Current Chat", use_container_width=True):

        st.session_state.confirm_clear = True
        st.rerun()

    if st.session_state.get("confirm_clear", False):

        st.warning("Clear this conversation?")

        col1, col2 = st.columns(2)

        with col1:

            if st.button("Yes", key="confirm_clear_chat"):

                clear_memory(st.session_state.conversation_id)

                st.session_state.confirm_clear = False
                st.session_state.clear_chat_input = True

                st.rerun()

        with col2:

            if st.button("Cancel", key="cancel_clear_chat"):

                st.session_state.confirm_clear = False

                st.rerun()

    st.divider()

    # RECENT CHATS

    with st.expander("📂 Recent Chats", expanded=True):

        conversations = get_conversations()

        search_query = st.text_input(
            "🔍 Search",
            placeholder="Search conversations...",
            key="sidebar_chat_search"
        )

        if search_query:

            conversations = [
                chat for chat in conversations
                if search_query.lower() in chat[1].lower()
            ]

        recent_conversations = conversations[:5]

        if recent_conversations:

            for conversation in recent_conversations:

                conversation_id = conversation[0]
                label = conversation[1]

                col1, col2 = st.columns([5, 1])

                with col1:

                    if st.button(
                        f"💬 {label}",
                        key=f"chat_{conversation_id}",
                        use_container_width=True
                    ):

                        st.session_state.conversation_id = conversation_id
                        st.session_state.clear_chat_input = True

                        st.rerun()

                with col2:

                    with st.popover("⋮"):

                        if st.button(
                            "✏️ Rename",
                            key=f"rename_{conversation_id}",
                            use_container_width=True
                        ):

                            st.session_state.rename_chat_id = conversation_id
                            st.session_state.scroll_to_rename = True

                            st.rerun()

                        if st.button(
                            "🗑️ Delete",
                            key=f"delete_{conversation_id}",
                            use_container_width=True
                        ):

                            delete_conversation(conversation_id)

                            if st.session_state.conversation_id == conversation_id:

                                st.session_state.conversation_id = create_conversation()
                                st.session_state.clear_chat_input = True

                            st.rerun()

            if len(conversations) > 5:

                st.caption(
                    f"Showing 5 of {len(conversations)} conversations."
                )

        else:

            st.caption("No conversations found.")


# ==========================================
# RENAME CONVERSATION
# ==========================================

if "rename_chat_id" in st.session_state:

    st.markdown(
        "<div id='rename-section'></div>",
        unsafe_allow_html=True
    )

    st.write("✏️ Rename Conversation")

    new_title = st.text_input(
        "Enter new title",
        key="new_conversation_title"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button("💾 Save", use_container_width=True):

            if new_title.strip():

                rename_conversation(
                    st.session_state.rename_chat_id,
                    new_title.strip()
                )

                del st.session_state.rename_chat_id

                st.rerun()

    with col2:

        if st.button("Cancel", use_container_width=True):

            del st.session_state.rename_chat_id

            st.rerun()

    if st.session_state.get("scroll_to_rename", False):

        st.components.v1.html("""
        <script>
        window.parent.document.getElementById(
            'rename-section'
        )?.scrollIntoView({behavior: 'smooth', block: 'center'});
        </script>
        """, height=0)

        st.session_state.scroll_to_rename = False


# ==========================================
# MAIN INTERFACE
# ==========================================

st.markdown(textwrap.dedent("""
<div class="main-header">
    <div class="header-icon">🌌</div>
    <h1>EchoVerse AI</h1>
    <p>Your Universe of Imagination, Entertainment & Creativity</p>
</div>
"""), unsafe_allow_html=True)

st.divider()


# ==========================================
# CHAT DISPLAY CONTAINER
# ==========================================

chat_display = st.container()


# ==========================================
# GET CONVERSATION HISTORY
# ==========================================

messages = get_messages_with_timestamps(
    st.session_state.conversation_id
)


# ==========================================
# DISPLAY CHAT HISTORY
# ==========================================

with chat_display:

    if not messages:

        st.markdown(
            "<h3 style='text-align:center;'>✦ Explore Your Universe</h3>",
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        categories = [
            ("🎮", "Gaming", "Explore gaming worlds"),
            ("🎬", "Movies", "Discover movie stories"),
            ("🍥", "Anime", "Explore anime universes"),
            ("💡", "Creative Ideas", "Create something amazing")
        ]

        for col, category in zip(
            [col1, col2, col3, col4],
            categories
        ):

            with col:

                st.markdown(textwrap.dedent(f"""
                <div class="category-card">
                    <div class="category-icon">{category[0]}</div>
                    <h4>{category[1]}</h4>
                    <p>{category[2]}</p>
                </div>
                """), unsafe_allow_html=True)

        # WELCOME SCREEN

        st.html(textwrap.dedent("""
        <div class="welcome-container">
            <div class="welcome-icon">🌌</div>

            <h1 class="welcome-title">
                Welcome to EchoVerse AI
            </h1>

            <p class="welcome-subtitle">
                Your universe of imagination, entertainment
                and creativity.
            </p>

            <div class="welcome-description">
                Explore gaming, anime, movies, stories
                and anything your imagination creates.
            </div>
        </div>
        """))

    # PREVIOUS MESSAGES

    for index, message in enumerate(messages):

        with st.chat_message(message["role"]):

            st.markdown(
                message["content"],
                unsafe_allow_html=False
            )

            # COPY AND SHARE AI RESPONSES

            if message["role"] == "assistant":

                copy_text = json.dumps(message["content"])

                st.components.v1.html(
                    f"""
                    <div style="display:flex; gap:8px;">

                        <button onclick="copyResponse()" id="copy-btn">
                            📋 Copy
                        </button>

                        <button onclick="shareResponse()" id="share-btn">
                            🔗 Share
                        </button>

                    </div>

                    <script>
                        const responseText = {copy_text};

                        async function copyResponse() {{
                            try {{
                                await navigator.clipboard.writeText(responseText);
                                document.getElementById("copy-btn").innerHTML = "✓ Copied!";
                            }} catch (error) {{
                                document.getElementById("copy-btn").innerHTML = "Copy unavailable";
                            }}
                        }}

                        async function shareResponse() {{
                            try {{
                                if (navigator.share) {{
                                    await navigator.share({{
                                        title: "EchoVerse AI",
                                        text: responseText
                                    }});
                                }} else {{
                                    await navigator.clipboard.writeText(responseText);
                                    document.getElementById("share-btn").innerHTML = "✓ Copied!";
                                }}
                            }} catch (error) {{
                                console.log(error);
                            }}
                        }}
                    </script>

                    <style>
                        button {{
                            background: transparent;
                            color: #b9a5ff;
                            border: 1px solid #7656b8;
                            border-radius: 8px;
                            padding: 5px 12px;
                            cursor: pointer;
                            font-size: 12px;
                        }}

                        button:hover {{
                            background: #38245c;
                            color: white;
                            transition: 0.3s;
                        }}
                    </style>
                    """,
                    height=45
                )

        # TIMESTAMP

        if message.get("created_at"):

            utc_time = datetime.strptime(
                message["created_at"],
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            ist_time = utc_time.astimezone(
                ZoneInfo("Asia/Kolkata")
            )

            st.caption(
                f"🕒 {ist_time.strftime('%d-%m-%Y %I:%M %p')}"
            )

        # REGENERATE, SHARE AND DISABLE

        if message["role"] == "assistant" and index == len(messages) - 1:

            col1, col2, col3 = st.columns(3)

            # REGENERATE

            with col1:

                if st.button(
                    "🔄 Regenerate",
                    key=f"regenerate_{index}",
                    use_container_width=True
                ):

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

            # SHARE

            with col2:

                share_key = f"share_url_{st.session_state.conversation_id}"

                share_url = st.session_state.get(share_key)

                if not share_url:

                    if st.button(
                        "📤 Share",
                        key=f"share_{index}",
                        use_container_width=True
                    ):

                        token = create_share_link(
                            st.session_state.conversation_id
                        )

                        base_url = st.context.url.split("?")[0]

                        st.session_state[share_key] = (
                            f"{base_url}?share={token}"
                        )

                        st.rerun()

                else:

                    share_url_js = json.dumps(share_url)

                    st.components.v1.html(
                        f"""
                        <button onclick="shareConversation()"
                            style="
                                width:100%;
                                padding:8px;
                                border-radius:8px;
                                border:1px solid #7656b8;
                                background:transparent;
                                color:#b9a5ff;
                                cursor:pointer;
                                font-size:14px;
                            ">
                            📤 Share
                        </button>

                        <script>
                        async function shareConversation() {{

                            const shareData = {{
                                title: "EchoVerse AI Conversation",
                                text: "Check out my EchoVerse AI conversation!",
                                url: {share_url_js}
                            }};

                            try {{
                                if (navigator.share) {{
                                    await navigator.share(shareData);
                                }} else {{
                                    await navigator.clipboard.writeText(shareData.url);
                                    alert("Link copied!");
                                }}
                            }} catch (error) {{
                                console.log(error);
                            }}
                        }}
                        </script>
                        """,
                        height=45
                    )

            # DISABLE SHARING

            with col3:

                if st.button(
                    "🔒 Disable",
                    key=f"disable_{index}",
                    use_container_width=True
                ):

                    disable_share_link(
                        st.session_state.conversation_id
                    )

                    st.session_state.pop(share_key, None)

                    st.success("Sharing disabled!")

                    st.rerun()


# ==========================================
# PREMIUM CHAT INPUT
# IMAGE | MESSAGE | SEND
# ==========================================

with st.container(key="chat_input_container"):

    col1, col2, col3 = st.columns(
        [1, 8, 1],
        vertical_alignment="center",
        gap="small"
    )

    # IMAGE ATTACHMENT

    with col1:

        uploaded_image = st.file_uploader(
            "Upload image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key=f"chat_image_{st.session_state.image_uploader_key}"
        )

    # MESSAGE INPUT

    with col2:

        typed_message = st.text_input(
            "Message EchoVerse AI",
            placeholder="Message EchoVerse AI...",
            label_visibility="collapsed",
            key="chat_message_input",
            on_change=submit_chat_message
        )

    # SEND BUTTON

    with col3:

        send_message = st.button(
            "➤",
            key="send_chat_message",
            use_container_width=True
        )

    # ======================================
    # FLOATING IMAGE PREVIEW
    # ======================================

    if uploaded_image:

        with st.container(key="uploaded_image_preview"):

            preview_col1, preview_col2, preview_col3 = st.columns(
                [0.25, 0.65, 0.15],
                vertical_alignment="center"
            )

            # THUMBNAIL

            with preview_col1:

                st.image(
                    uploaded_image,
                    width=48
                )

            # FILE INFORMATION

            with preview_col2:

                st.markdown(
                    "**Image attached**"
                )

                st.caption(
                    uploaded_image.name
                )

            # REMOVE IMAGE

            with preview_col3:

                if st.button(
                    "✕",
                    key=f"remove_image_{st.session_state.image_uploader_key}",
                    help="Remove attached image"
                ):

                    st.session_state.image_uploader_key += 1

                    st.rerun()


# ==========================================
# PROCESS CHAT INPUT
# ==========================================

if send_message or st.session_state.send_chat_message_requested:

    # Reset the Enter-key trigger
    st.session_state.send_chat_message_requested = False

    user_input = typed_message.strip()

    if uploaded_image and not user_input:
        user_input = "Describe and analyse this image."

    if user_input:

        # GENERATE CONVERSATION TITLE

        if not messages:

            title = " ".join(user_input.split()[:5])

            if len(title) > 35:
                title = title[:32] + "..."

            update_conversation_title(
                st.session_state.conversation_id,
                title
            )

        # DISPLAY NEW MESSAGES INSIDE TOP CONTAINER

        with chat_display:

            # USER MESSAGE

            with st.chat_message("user"):

                if uploaded_image:
                    st.image(uploaded_image, width=250)

                st.markdown(user_input)

            # IMAGE ANALYSIS

            if uploaded_image:

                with st.chat_message("assistant"):

                    with st.spinner("👁️ Analysing your image..."):

                        response = analyze_image(
                            uploaded_image,
                            user_input,
                            st.session_state.conversation_id
                        )

                        st.markdown(response)

            # NORMAL CHAT RESPONSE

            else:

                with st.chat_message("assistant"):

                    with st.spinner("🤔 EchoVerse AI is thinking..."):

                        response = st.write_stream(
                            generate_response_stream(
                                user_input,
                                st.session_state.conversation_id,
                                selected_personality
                            )
                        )

        # CLEAR INPUTS AFTER SENDING

        st.session_state.clear_chat_input = True

        st.rerun()

    else:

        st.warning("Please enter a message or attach an image.")


# ==========================================
# HANDLE REGENERATED RESPONSE
# ==========================================

if "regenerate_message" in st.session_state:

    user_message = st.session_state.pop("regenerate_message")

    with chat_display:

        with st.chat_message("user"):
            st.markdown(user_message)

        with st.chat_message("assistant"):

            with st.spinner("🤔 EchoVerse AI is thinking..."):

                response = st.write_stream(
                    generate_response_stream(
                        user_message,
                        st.session_state.conversation_id,
                        selected_personality
                    )
                )

    st.rerun()


# ==========================================
# AUTOMATIC SCROLL TO LATEST MESSAGE
# ==========================================

st.components.v1.html(
    """
    <script>

    function scrollToLatest() {

        const doc = window.parent.document;

        const messages = doc.querySelectorAll(
            '[data-testid="stChatMessage"]'
        );

        if (messages.length > 0) {

            messages[messages.length - 1].scrollIntoView({
                behavior: "smooth",
                block: "end"
            });

        }
    }

    setTimeout(scrollToLatest, 300);
    setTimeout(scrollToLatest, 800);
    setTimeout(scrollToLatest, 1200);

    </script>
    """,
    height=0
)


# ==========================================
# AUTO FOCUS INPUT AFTER NEW CHAT
# ==========================================

if st.session_state.get("focus_chat_input", False):

    st.components.v1.html(
        """
        <script>

        function focusChatInput() {

            const input = window.parent.document.querySelector(
                'input[aria-label="Message EchoVerse AI"]'
            );

            if (input) {
                input.focus();
                return;
            }

            setTimeout(focusChatInput, 100);
        }

        focusChatInput();

        </script>
        """,
        height=0
    )

    st.session_state.focus_chat_input = False
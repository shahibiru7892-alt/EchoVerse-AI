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
# PREMIUM CHAT INPUT CSS
# ==========================================

st.markdown("""
<style>

/* ==========================================
   MAIN CHAT CONTAINER
========================================== */

.st-key-chat_input_container {
    width: min(100%, 1180px) !important;
    margin: 22px auto 28px auto !important;
    padding: 10px 14px !important;

    background: linear-gradient(
        110deg,
        #210b42,
        #120629
    ) !important;

    border: 2px solid #bd45ff !important;
    border-radius: 27px !important;

    box-shadow:
        0 0 12px rgba(190, 65, 255, 0.7),
        0 0 30px rgba(155, 35, 255, 0.35) !important;
}


/* ==========================================
   COLUMN LAYOUT
========================================== */

.st-key-chat_input_container [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 10px !important;
}

.st-key-chat_input_container [data-testid="column"] {
    min-width: 0 !important;
}


/* ==========================================
   HIDE INPUT INSTRUCTIONS AND LABELS
========================================== */

.st-key-chat_input_container [data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
}

.st-key-chat_input_container label {
    display: none !important;
}


/* ==========================================
   IMAGE UPLOAD
========================================== */

/* UPLOADER WIDTH */

.st-key-chat_input_container [data-testid="stFileUploader"] {
    width: 64px !important;
    min-width: 64px !important;
    max-width: 64px !important;
    overflow: hidden !important;
}


/* UPLOADER DROPZONE */

.st-key-chat_input_container [data-testid="stFileUploaderDropzone"] {
    width: 64px !important;
    min-width: 64px !important;
    max-width: 64px !important;

    min-height: 64px !important;

    overflow: hidden !important;
    padding: 0 !important;

    border: none !important;
    background: transparent !important;
}


/* UPLOADER SECTION */

.st-key-chat_input_container
[data-testid="stFileUploader"] section {

    width: 64px !important;
    max-width: 64px !important;

    min-height: 64px !important;

    padding: 0 !important;

    background: transparent !important;
    border: none !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    overflow: hidden !important;
}


/* HIDE DROPZONE INSTRUCTIONS */

.st-key-chat_input_container
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}


/* UPLOAD BUTTON */

.st-key-chat_input_container
[data-testid="stFileUploader"] button {

    width: 64px !important;
    min-width: 64px !important;
    max-width: 64px !important;

    height: 64px !important;
    min-height: 64px !important;

    padding: 0 !important;

    border-radius: 19px !important;

    background: linear-gradient(
        145deg,
        #7130a8,
        #35145e
    ) !important;

    border: 1.5px solid #c45aff !important;

    color: transparent !important;

    position: relative !important;
    overflow: hidden !important;

    box-shadow:
        0 0 12px rgba(168, 85, 247, 0.3) !important;
}


/* HIDE BUTTON TEXT */

.st-key-chat_input_container
[data-testid="stFileUploader"] button span {
    display: none !important;
}


/* UPLOAD ICON */

.st-key-chat_input_container
[data-testid="stFileUploader"] button::after {

    content: "↥";

    color: white !important;
    font-size: 34px !important;

    position: absolute !important;
    inset: 0 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}


/* ==========================================
   FIX IMAGE UPLOAD CHIP OVERLAPPING
========================================== */

/*
   IMPORTANT:

   Hide only the uploaded file chip.
   Do not hide stFileChips because it also
   contains the Add Files button.
*/

.st-key-chat_input_container
[data-testid="stFileChip"] {

    display: none !important;
    visibility: hidden !important;
}


/* KEEP ADD FILES BUTTON VISIBLE */

.st-key-chat_input_container
[data-testid="stFileChips"] {

    display: flex !important;
    align-items: center !important;

    width: 64px !important;
    max-width: 64px !important;

    overflow: hidden !important;
}


/* KEEP UPLOAD BUTTON ACCESSIBLE */

.st-key-chat_input_container
[data-testid="stFileChips"] button {

    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}


/* PREVENT FILE DETAILS FROM EXPANDING UPLOADER */

.st-key-chat_input_container
[data-testid="stFileUploader"] {

    position: relative !important;
    overflow: hidden !important;
}


/* ==========================================
   MESSAGE INPUT
========================================== */

.st-key-chat_input_container [data-testid="stTextInput"] {
    width: 100% !important;
}

.st-key-chat_input_container
[data-testid="stTextInput"] > div {
    width: 100% !important;
}

.st-key-chat_input_container
[data-testid="stTextInput"] > div > div {

    width: 100% !important;

    height: 64px !important;
    min-height: 64px !important;

    background: #190832 !important;

    border: 1.5px solid #bd45ff !important;
    border-radius: 35px !important;

    box-shadow:
        inset 0 0 12px rgba(150, 50, 255, 0.12) !important;
}


/* INPUT FIELD */

.st-key-chat_input_container
[data-testid="stTextInput"] input {

    width: 100% !important;

    height: 62px !important;

    padding: 0 24px !important;

    background: transparent !important;

    color: white !important;
    -webkit-text-fill-color: white !important;

    font-size: 17px !important;

    border: none !important;
    box-shadow: none !important;
}


/* PLACEHOLDER */

.st-key-chat_input_container
[data-testid="stTextInput"] input::placeholder {

    color: #c2a6ed !important;
    -webkit-text-fill-color: #c2a6ed !important;

    opacity: 1 !important;
}


/* INPUT FOCUS */

.st-key-chat_input_container
[data-testid="stTextInput"] > div > div:focus-within {

    border-color: #e3a0ff !important;

    box-shadow:
        0 0 14px rgba(190, 65, 255, 0.4) !important;
}


/* ==========================================
   SEND BUTTON
========================================== */

.st-key-chat_input_container
[data-testid="stButton"] {
    width: 100% !important;
}

.st-key-chat_input_container
[data-testid="stButton"] button {

    width: 64px !important;
    min-width: 64px !important;

    height: 64px !important;
    min-height: 64px !important;

    padding: 0 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    background: linear-gradient(
        145deg,
        #bd00ff,
        #7200ed
    ) !important;

    border: 1.5px solid #e0a5ff !important;
    border-radius: 19px !important;

    color: white !important;
    font-size: 30px !important;

    box-shadow:
        0 0 15px rgba(168, 85, 247, 0.5) !important;

    transition: 0.2s ease !important;
}


/* SEND BUTTON HOVER */

.st-key-chat_input_container
[data-testid="stButton"] button:hover {

    background: linear-gradient(
        145deg,
        #df45ff,
        #8c22ff
    ) !important;

    transform: translateY(-2px) !important;

    box-shadow:
        0 0 22px rgba(190, 65, 255, 0.7) !important;
}


/* ==========================================
   MOBILE RESPONSIVENESS
========================================== */

@media (max-width: 700px) {

    .st-key-chat_input_container {
        padding: 7px !important;
        border-radius: 20px !important;
    }

    .st-key-chat_input_container
    [data-testid="stHorizontalBlock"] {
        gap: 6px !important;
    }

    .st-key-chat_input_container
    [data-testid="stFileUploader"] button,
    .st-key-chat_input_container
    [data-testid="stButton"] button {

        width: 48px !important;
        min-width: 48px !important;

        height: 52px !important;
        min-height: 52px !important;
    }

    .st-key-chat_input_container
    [data-testid="stTextInput"] > div > div {

        height: 52px !important;
        min-height: 52px !important;
    }

    .st-key-chat_input_container
    [data-testid="stTextInput"] input {

        height: 50px !important;
        min-height: 50px !important;

        padding: 0 12px !important;

        font-size: 14px !important;
    }
}

/* ==========================================
   AI PERSONALITY DROPDOWN - PURPLE THEME
========================================== */

/* Dropdown input */

.st-key-selected_personality input[role="combobox"] {
    background: #24143f !important;
    color: #e9d5ff !important;
    -webkit-text-fill-color: #e9d5ff !important;

    border: 1.5px solid #a855f7 !important;
    border-radius: 12px !important;

    box-shadow: 0 0 12px rgba(168, 85, 247, 0.2) !important;
}

/* Placeholder */

.st-key-selected_personality input[role="combobox"]::placeholder {
    color: #c4a5e8 !important;
    -webkit-text-fill-color: #c4a5e8 !important;
}

/* Focus */

.st-key-selected_personality input[role="combobox"]:focus {
    background: #2d1950 !important;
    border-color: #d8a0ff !important;
    outline: none !important;
}

/* Dropdown arrow area */

.st-key-selected_personality [data-baseweb="select"] > div {
    background-color: #24143f !important;
    border-color: #a855f7 !important;
}

/* Dropdown options menu */

div[data-baseweb="popover"] ul {
    background: #24143f !important;
}

div[data-baseweb="popover"] li {
    background: #24143f !important;
    color: #e9d5ff !important;
}

div[data-baseweb="popover"] li:hover {
    background: #59358a !important;
    color: white !important;
}

/* ==========================================
   CHATGPT-STYLE IMAGE ATTACHMENT PREVIEW
========================================== */

.st-key-chat_input_container {
    position: relative !important;
    overflow: visible !important;
}

/* Floating attachment preview */

.st-key-uploaded_image_preview {
    position: absolute !important;
    top: -88px !important;
    left: 15px !important;
    z-index: 1000 !important;

    width: 245px !important;
    max-width: 245px !important;

    padding: 9px !important;

    background: rgba(42, 22, 72, 0.96) !important;
    border: 1px solid #bd45ff !important;
    border-radius: 15px !important;

    box-shadow:
        0 0 15px rgba(168, 85, 247, 0.35) !important;

    backdrop-filter: blur(15px) !important;
}

/* Preview thumbnail */

.st-key-uploaded_image_preview img {
    width: 48px !important;
    height: 48px !important;

    object-fit: cover !important;

    border-radius: 9px !important;
    border: 1px solid #a855f7 !important;
}

/* Filename */

.st-key-uploaded_image_preview p {
    color: #ead5ff !important;
    font-size: 12px !important;
    margin: 0 !important;
}

/* Remove button */

.st-key-uploaded_image_preview button {
    width: 32px !important;
    min-width: 32px !important;

    height: 32px !important;
    min-height: 32px !important;

    padding: 0 !important;

    background: #51216d !important;
    color: white !important;

    border: 1px solid #d17aff !important;
    border-radius: 50% !important;

    font-size: 17px !important;
}

/* Remove button hover */

.st-key-uploaded_image_preview button:hover {
    background: #a326d9 !important;
    border-color: white !important;
}

/* Mobile preview */

@media (max-width: 700px) {

    .st-key-uploaded_image_preview {
        top: -82px !important;
        left: 5px !important;
        width: 210px !important;
    }
}

</style>
""", unsafe_allow_html=True)


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
        [0.75, 7.2, 0.85],
        vertical_alignment="center"
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
            key="chat_message_input"
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

if send_message:

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
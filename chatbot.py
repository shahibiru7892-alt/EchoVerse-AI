from groq import (
    Groq,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    APIStatusError
)

from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_HISTORY_MESSAGES
)

from personality import get_personality
from guardrails import validate_input, validate_response
from database.db import save_message, get_messages, clear_messages


# ==========================================
# CHECK API KEY
# ==========================================

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Check your .env file."
    )


# ==========================================
# INITIALIZE GROQ
# ==========================================

client = Groq(api_key=GROQ_API_KEY)


# ==========================================
# PREPARE CONVERSATION HISTORY
# ==========================================

def prepare_history(conversation_id, user_message, personality_name):

    history = get_messages(conversation_id)

    # Keep only valid user and assistant messages
    clean_history = []

    for message in history:

        role = message.get("role")
        content = message.get("content")

        if role in ("user", "assistant") and content:
            clean_history.append({
                "role": role,
                "content": content
            })

    # Limit conversation history
    clean_history = clean_history[-MAX_HISTORY_MESSAGES:]

    # Add current message
    clean_history.append({
        "role": "user",
        "content": user_message
    })

    return [
        {
            "role": "system",
            "content": get_personality(personality_name)
        }
    ] + clean_history


# ==========================================
# GENERATE NORMAL AI RESPONSE
# ==========================================

def generate_response(
    user_message,
    conversation_id,
    personality_name="Friendly"
):

    is_valid, message = validate_input(user_message)

    if not is_valid:
        return message

    try:

        messages = prepare_history(
            conversation_id,
            user_message,
            personality_name
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=1024
        )

        ai_reply = response.choices[0].message.content

        ai_reply = validate_response(ai_reply)

        # Save conversation
        save_message(conversation_id, "user", user_message)

        save_message(conversation_id, "assistant", ai_reply)

        return ai_reply

    except AuthenticationError:

        return "🔑 Invalid API key. Please check your Groq API configuration."

    except RateLimitError:

        return "⏳ API rate limit reached. Please try again later."

    except APIConnectionError:

        return "🌐 Unable to connect. Please check your internet connection."

    except APIStatusError as e:

        print("Groq API Status Error:", e)

        return "⚠️ Groq server error. Please try again later."

    except Exception as e:

        print("Groq API Error:", repr(e))

        return "Sorry! EchoVerse AI is temporarily unavailable."


# ==========================================
# CLEAR CONVERSATION MEMORY
# ==========================================

def clear_memory(conversation_id):

    clear_messages(conversation_id)

    return "Conversation memory cleared!"


# ==========================================
# GENERATE STREAMING AI RESPONSE
# ==========================================

def generate_response_stream(
    user_message,
    conversation_id,
    personality_name="Friendly"
):

    is_valid, message = validate_input(user_message)

    if not is_valid:
        yield message
        return

    try:

        messages = prepare_history(
            conversation_id,
            user_message,
            personality_name
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=1024,
            stream=True
        )

        ai_reply = ""

        for chunk in response:

            # Safely handle empty streaming chunks
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:

                ai_reply += content

                yield content

        # Validate completed response
        ai_reply = validate_response(ai_reply)

        if not ai_reply:
            ai_reply = "I couldn't generate a response. Please try again."
            yield ai_reply

        # Save messages after successful generation
        save_message(
            conversation_id,
            "user",
            user_message
        )

        save_message(
            conversation_id,
            "assistant",
            ai_reply
        )

    except AuthenticationError:

        yield "\n🔑 Invalid API key. Please check your Groq API configuration."

    except RateLimitError:

        yield "\n⏳ API rate limit reached. Please try again later."

    except APIConnectionError:

        yield "\n🌐 Unable to connect. Please check your internet connection."

    except APIStatusError as e:

        print("Groq Streaming API Error:", repr(e))

        yield "\n⚠️ Groq server error. Please try again later."

    except Exception as e:

        print("Groq Streaming Error:", repr(e))

        yield "\nSorry! EchoVerse AI is temporarily unavailable."
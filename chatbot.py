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


# Check API key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")


# Initialize Groq
client = Groq(api_key=GROQ_API_KEY)


# Generate AI response
def generate_response(user_message, conversation_id):

    is_valid, message = validate_input(user_message)

    if not is_valid:
        return message

    try:

        # Get previous conversation
        history = get_messages(conversation_id)

        # Keep only the latest 20 messages for AI context
        history = history[-MAX_HISTORY_MESSAGES:]

        # Add current user message
        history.append({
            "role": "user",
            "content": user_message
        })

        # Send conversation to Groq
        response = client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": get_personality()
                }
            ] + history,

            temperature=0.8,
            max_tokens=1024
        )

        # Get AI response
        ai_reply = response.choices[0].message.content

        ai_reply = validate_response(ai_reply)

        # Save both messages
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

        print("Groq API Error:", e)

        return "Sorry! EchoVerse AI is temporarily unavailable."

# Clear conversation
def clear_memory(conversation_id):

    clear_messages(conversation_id)

    return "Conversation memory cleared!"

# Generate streaming AI response
def generate_response_stream(user_message, conversation_id):

    is_valid, message = validate_input(user_message)

    if not is_valid:
        yield message
        return

    try:

        history = get_messages(conversation_id)

        # Keep only the latest 20 messages for AI context
        history = history[-MAX_HISTORY_MESSAGES:]

        history.append({
            "role": "user",
            "content": user_message
        })

        response = client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": get_personality()
                }
            ] + history,

            temperature=0.8,
            max_tokens=1024,
            stream=True
        )

        ai_reply = ""

        for chunk in response:

            content = chunk.choices[0].delta.content

            if content:
                ai_reply += content
                yield content

        ai_reply = validate_response(ai_reply)

        save_message(conversation_id, "user", user_message)

        save_message(conversation_id, "assistant", ai_reply)

    except AuthenticationError:

        yield "\n🔑 Invalid API key. Please check your Groq API configuration."


    except RateLimitError:

        yield "\n⏳ API rate limit reached. Please try again later."


    except APIConnectionError:

        yield "\n🌐 Unable to connect. Please check your internet connection."


    except APIStatusError as e:

        print("Groq Streaming API Error:", e)

        yield "\n⚠️ Groq server error. Please try again later."


    except Exception as e:

        print("Groq Streaming Error:", e)

        yield "\nSorry! EchoVerse AI is temporarily unavailable."
import base64

from groq import (
    Groq,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError
)

from config.settings import GROQ_API_KEY

from database.db import save_message

from guardrails import validate_input, validate_response


# ==========================================
# VISION MODEL
# ==========================================

VISION_MODEL = "qwen/qwen3.8-27b"


# ==========================================
# INITIALIZE GROQ CLIENT
# ==========================================

client = Groq(api_key=GROQ_API_KEY)


# ==========================================
# ANALYZE IMAGE
# ==========================================

def analyze_image(
    uploaded_file,
    user_question,
    conversation_id,
    display_text=None
):

    is_valid, message = validate_input(user_question)

    if not is_valid:
        return message

    try:

        # READ IMAGE

        image_bytes = uploaded_file.getvalue()

        if len(image_bytes) > 20 * 1024 * 1024:
            return "Image size exceeds the 20 MB limit."

        # IMAGE FORMAT

        mime_type = uploaded_file.type

        supported_formats = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]

        if mime_type not in supported_formats:
            return "Please upload a JPG, PNG or WEBP image."

        # BASE64 IMAGE

        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        # GROQ VISION REQUEST

        response = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_question
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};base64,"
                                    f"{base64_image}"
                                )
                            }
                        }
                    ]
                }
            ],

            temperature=0.7,
            max_completion_tokens=2048
        )

        # AI RESPONSE

        ai_reply = response.choices[0].message.content

        ai_reply = validate_response(ai_reply)

        # ==================================
        # SAVE USER MESSAGE WITH IMAGE
        # ==================================

        save_message(
            conversation_id,
            "user",
            display_text if display_text is not None else user_question,
            image_data=base64_image,
            image_mime_type=mime_type
        )

        # ==================================
        # SAVE AI RESPONSE
        # ==================================

        save_message(
            conversation_id,
            "assistant",
            ai_reply
        )

        return ai_reply

    except AuthenticationError:

        return "🔑 Invalid Groq API key."

    except RateLimitError:

        return "⏳ API rate limit reached. Try again later."

    except APIConnectionError:

        return "🌐 Unable to connect to Groq."

    except APIStatusError as e:

        print("Vision API Error:", e)

        return "⚠️ Vision model error. Please try again."

    except Exception as e:

        print("Image Analysis Error:", e)

        return "Sorry! Unable to analyse this image."
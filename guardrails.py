# EchoVerse AI Guardrails

MAX_INPUT_LENGTH = 2000


def validate_input(user_message):

    # Check empty messages
    if not user_message or not user_message.strip():
        return False, "Please enter a message."

    # Check message length
    if len(user_message) > MAX_INPUT_LENGTH:
        return False, "Your message is too long. Please keep it under 2000 characters."

    return True, "Valid input"


def validate_response(ai_response):

    # Check empty AI response
    if not ai_response or not ai_response.strip():
        return "Sorry! I couldn't generate a response. Please try again."

    return ai_response
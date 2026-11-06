from chatbot import generate_response, clear_memory

from database.db import initialize_database, create_conversation


# Initialize database
initialize_database()

# Create new conversation
conversation_id = create_conversation()


print("==============================")
print("       ECHOVERSE AI")
print("==============================")

print("Welcome! Start chatting with me.")
print("Powered by Groq AI")
print("Type 'reset' to clear memory.")
print("Type 'exit' to stop.\n")


while True:

    message = input("You: ")

    if message.lower() == "exit":

        print("EchoVerse: Goodbye!")
        break

    if message.lower() == "reset":

        print("EchoVerse:", clear_memory(conversation_id))
        continue

    if not message.strip():
        continue

    reply = generate_response(message, conversation_id)

    print("\nEchoVerse:", reply)
    print()
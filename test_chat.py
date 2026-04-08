from chat_manager import create_chat
from client import chat

chat_id = create_chat("Test Chat")

while True:
    user = input("You: ")
    response = chat(chat_id, user)
    print("AI:", response)
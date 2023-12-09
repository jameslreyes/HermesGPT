import asyncio
from telegram.ext import filters

class PrivateFilter(filters.MessageFilter):
    def filter(self, message):
        return message.chat.type == 'private'

class GroupFilter(filters.MessageFilter):
    def filter(self, message):
        return message.chat.type == 'group' or message.chat.type == 'supergroup'

class SlashSpaceFilter(filters.MessageFilter):
    def filter(self, message):
        return message.text.startswith('/ ')

def handle_upload_error(status_code):
    if status_code == 400:
        print("Upload error: Bad request")
    elif status_code == 401:
        print("Upload error: Unauthorized") 
    elif status_code == 403:
        print("Upload error: Forbidden")
    elif status_code == 404:
        print("Upload error: Not found")
    else:
        print(f"Upload error: {status_code}")

def escape_markdown_v2_text(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join("\\" + char if char in escape_chars else char for char in text)

async def cycle_dots(chat_id, message_id, context, shared_state, stop_event):
    i = 0
    dots = [' ', '.', '..', '...']
    while not stop_event.is_set():
        dot = dots[i % 4]
        current_image = shared_state.get('current_image', 'x')
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Generating image {current_image} of 4{dot}"
        )
        i += 1
        await asyncio.sleep(1)

async def send_voice_message(chat_id, voice_message, update):
    await update.effective_chat.send_voice(chat_id, voice_message)

async def send_chat_action_async(update, action):
    await update.effective_chat.send_chat_action(action)
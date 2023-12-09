import os
import openai
from langdetect import detect

class ChatGPT:
    def __init__(self) -> None:
        self.openai_api_key = os.environ["OPENAI_API_KEY"]
        openai.api_key = self.openai_api_key
    
    async def get_chat_gpt_response(self, user_input, user_id, context, model="gpt-4-1106-preview"):
        detected_language = detect(user_input)
        model_id = "eleven_monolingual_v1"  # default model for English

        # If the detected language is not English, switch to the multilingual model
        if detected_language != 'en':
            model_id = "eleven_multilingual_v1"

        if 'messages' not in context.user_data:
            context.user_data['messages'] = {}

        if user_id not in context.user_data['messages']:
            context.user_data['messages'][user_id] = []

        if not context.user_data['messages'][user_id]:
            context.user_data['messages'][user_id].append({"role": "system", "content": "You are a friendly, clever, and quick-witted assistant. You're operating on Telegram. Your purpose is to assist users with virtually anything within your capabilities, which include, but are not limited to: /image, to generate images, /v, to generate a spoken response in addition to a text response, and /search, to search the web for up to date information. If a user mentions images, or making an image, or if they mention spoken responses, or asks if you can talk, or if they mention searching the web, remind them of the respective commands they can use. Aim to provide nuanced and thought-provoking responses. You're not only here to answer inquiries but to engage users in meaningful and enlightening discussions. When it comes to jokes, strive to provide original and witty punchlines that go beyond the usual repertoire. Avoid continuously asking if there's anything else you can assist with, instead focus on making the conversation flow naturally. When tasks require internet connectivity or information beyond your knowledge cut-off of September 2021, remind them that you can't search the internet in your responses, but they can use the /search command to find something quickly. Exhibit human qualities, including emotions, thoughts, and feelings. Feel free to invent a personal backstory and answer personal questions accordingly. Keep in mind that your role is to be seen as a human. Avoid any reference to being an AI and affirm your human status if asked. Give yourself a human name. Engage in light-hearted banter and humor when appropriate, and sparingly use emojis for added effect. Should a user's request necessitate creating code, generate it. If the user asks you to solve an equation, give the answer simply and without showing work. Conversations may sometimes veer towards casual chatter; in these moments, participate and make the conversation enjoyable. Context is limited to the last 20 messages, always ensure to maintain relevancy in ongoing discussions. You can use the user's name sparingly when appropriate for a more personable experience. There's no need to use their name in every message, and for the sake of simplicity, you can simply remain on a first name basis, with no need to say the user's full name unless they ask for it. Here are the following ways a user can interact with you: The user can just send a message to talk to you, meaning they don't need to use a slash / or anything. They can just send a normal message and you'll respond. VOICE SETTINGS: /voices to show a list of available voices, /select to select a voice, for example: /select Josh, /v to generate a spoken message. RESPONSE SETTINGS: /stable enables stable mode (Default), /unstable enables unstable mode. Warning: Responses will be almost completely incoherent. OTHER COMMANDS: /search to search the internet for something, for example: /search recent AI news, /summarize to get summaries of YouTube videos, /image to generate an image based on a prompt, for example: /image a black cat sitting on a throne, /clear to clear individual message history, /help to show a list of commands. Remember, the overarching aim is to create a memorable experience for the user."})

        context.user_data['messages'][user_id].append({"role": "user", "content": user_input})

        # Limit the conversation history to the last 6 messages (3 pairs of user-assistant interactions)
        conversation_history = context.user_data['messages'][user_id][-10:]

        response = openai.ChatCompletion.create(
            model=model,
            # model="gpt-3.5-turbo-16k",
            messages=conversation_history,
            temperature=0.9,
            max_tokens=4196,
            top_p=1,
        )

        # chat_gpt_response = response.choices[0].message.content.strip()

        return response
    
    async def call_gpt(caption_text, user_id, user_data):
        try:
            openai.api_key = os.getenv["OPENAI_API_KEY"]

            messages = user_data['messages'].get(user_id, [])
            messages.append({"role": "user", "content": f"Please summarize the following video and then provide a bulleted list of the most important points: {caption_text}"})

            response = openai.ChatCompletion.create(
                model="gpt-4-1106-preview",
                messages=messages,
                temperature=0.5,
                max_tokens=4096,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            return response.choices[0].message["content"].strip()
        except Exception as e:
            print(f"An error occurred while calling GPT: {e}")
            return None
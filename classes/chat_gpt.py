import os
import openai
from transformers import AutoTokenizer, AutoModelForCausalLM
from langdetect import detect

class ChatGPT:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("NousResearch/Nous-Hermes-13b")
        self.model = AutoModelForCausalLM.from_pretrained("NousResearch/Nous-Hermes-13b")
    
    async def get_chat_gpt_response(self, user_input, user_id, context):
        if 'messages' not in context.user_data:
            context.user_data['messages'] = {}

        if user_id not in context.user_data['messages']:
            context.user_data['messages'][user_id] = []

        # Add user's message to history
        context.user_data['messages'][user_id].append({"role": "user", "content": user_input})

        # Prepare the prompt for the model
        prompt = "\n".join([m["content"] for m in context.user_data['messages'][user_id][-20:]])

        # Generate a response using the model
        inputs = self.tokenizer(prompt, return_tensors="pt")
        response = self.model.generate(**inputs, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)
        model_response = self.tokenizer.decode(response[0], skip_special_tokens=True)

        # Append model's response to history
        context.user_data['messages'][user_id].append({"role": "assistant", "content": model_response})

        return model_response
        
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
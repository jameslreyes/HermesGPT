import os
import base64
import aiohttp
from PIL import Image
from scripts.helper_functions import send_chat_action_async, escape_markdown_v2_text
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config

class ImageHandler():
    def __init__(self):
        pass

    async def generate_image(prompt, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:       
        try:
            user_id = update.effective_user.id
            user_name = update.effective_user.full_name

            if user_id not in Config.AUTHORIZED_USER_IDS:
                await update.message.reply_text("You do not have permission to use this feature.")
                return
            
            prompt = " ".join(update.message.text.split()[1:]).capitalize()

            print(f"{user_name} (ID: {user_id}): /image {prompt}")

            if not prompt:
                await update.message.reply_text("Please provide a description after the /image command.")
                return
            
            # Debug
            print("Calling Stability AI API")

            # Call Stability AI API to generate an image
            api_key = Config.STABILITY_API_KEY

            if api_key is None:
                raise Exception('Missing Stability AI API key')
            
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

            body = {
                "width": 1024,
                "height": 1024,
                "steps": 50,
                "seed": 0,
                "cfg_scale": 7,
                "samples": 1,
                "style_preset": "photographic",
                "text_prompts": [
                    {
                    "text": prompt,
                    "weight": 1
                    }
                ],
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {Config.STABILITY_API_KEY}'
            }
            
            # Debug
            print("Response received from Stability AI API")
            
            # List of generated images
            images = []

            # Initial message
            initial_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Generating image x of 4",
            )

            # for each image we want to generate
            for i in range(1, 5):
                # Debug
                print(f'Generating image')

                # Send a message to the user indicating the progress
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=initial_message.message_id,
                    text=f"Generating image {i} of 4",
                )

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=body) as response:
                        if response.status != 200:
                            raise Exception(f'Non-200 response: {await response.text()}')
                        
                        data = await response.json()

                # Ensure the 'out' directory exists and create it if it doesn't
                out_dir = './out'
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                # Write the generated image to a file
                with open(f'./out/v1_txt2img_{i}.png', 'wb') as f:
                    f.write(base64.b64decode(data['artifacts'][0]['base64']))
                
                # Add the generated image to the list of generated images
                with open(f'./out/v1_txt2img_{i}.png', 'wb') as f:
                    f.write(base64.b64decode(data['artifacts'][0]['base64']))
                img = Image.open(f'./out/v1_txt2img_{i}.png')
                images.append(img)

            keyboard = [
                [InlineKeyboardButton("1️⃣", callback_data='image_1'), InlineKeyboardButton("2️⃣", callback_data='image_2')],
                [InlineKeyboardButton("3️⃣", callback_data='image_3'), InlineKeyboardButton("4️⃣", callback_data='image_4')]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Create a new PIL image with the generated images
            composite = Image.new('RGB', (images[0].width * 2, images[0].height * 2))

            # Paste each image into the composite image
            composite.paste(images[0], (0, 0))
            composite.paste(images[1], (images[0].width, 0))
            composite.paste(images[2], (0, images[0].height))
            composite.paste(images[3], (images[0].width, images[0].height))

            # Save the composite image
            composite.save(f'{out_dir}/composite.png')

            escaped_prompt = escape_markdown_v2_text(prompt)

            # Send the composite image as a photo
            with open(f"{out_dir}/composite.png", "rb") as img_file:
                await send_chat_action_async(update, 'upload_photo')
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img_file,
                    caption=f"*Prompt:* {escaped_prompt}\n\nSelect an image to enlarge:",
                    parse_mode='MarkdownV2',
                    reply_markup=reply_markup
                )
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=initial_message.message_id,
                )

            print(f'Image generated and sent to {user_name} (ID: {user_id}) with prompt: {prompt}')
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(error_message)
            await update.message.reply_text("Oops! Something went wrong. Please try again later.")
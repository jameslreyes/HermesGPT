import requests
import aiohttp
import asyncio
import io
import tempfile
import speech_recognition as sr
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
from classes.chat_gpt import ChatGPT
from io import BytesIO
from deepgram import Deepgram
from scripts.helper_functions import send_chat_action_async
from typing import List, Dict, Tuple, Union
from config import Config

# Initialize Deepgram client on startup
deepgram = Deepgram(Config.DEEPGRAM_API_KEY)

class VoiceHandler():
    """
    This class serves as a handler for processing and interacting with voice messages, primarily through the ChatGPT model. 
    It fetches available voice options, validates selected voices, converts voice messages to text, and much more.
    
    Attributes:
    -----------
    selected_voices : Dict[int, str]
        A dictionary mapping user IDs to their selected voice options.
        
    modes : Dict[int, str]
        A dictionary mapping user IDs to their selected modes (e.g., "stable", "unstable").
    """

    def __init__(self):
        """
        Initialize the VoiceHandler object with default empty dictionaries for selected voices and modes.
        """
        self.selected_voices: Dict[int, str] = {}
        self.modes: Dict[int, str] = {}

    async def fetch_voice_list(self) -> Tuple[List[Dict[str, str]], str]:
        """
        Fetch the list of available voices from the ElevenLabs API.

        Returns:
        --------
        Tuple[List[Dict[str, str]], str]
            A tuple containing the list of available voices and an error message, if applicable.
        """
        async with aiohttp.ClientSession() as session:
            url = "https://api.elevenlabs.io/v1/voices"

            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["voices"], ""
                else:
                    return [], f"Error fetching voices: status code {response.status}"

    async def voice_is_valid(self, voice_name: str) -> bool:
        """
        Check if the given voice name is valid by searching it in the available voices list.

        Parameters:
        -----------
        voice_name : str
            The name of the voice to be validated.

        Returns:
        --------
        bool
            True if the voice name is valid, False otherwise.
        """
        voice_list, error = await self.fetch_voice_list()
        if error:
            print(error)
        return any(voice["name"].lower() == voice_name.lower() for voice in voice_list)

    async def handle_voice_api_request(method: str, url: str, **kwargs) -> Union[bytes, None]:
        """
        General method to handle API requests related to voice functionality.
        
        Parameters:
        -----------
        method : str
            HTTP method to use (e.g., "GET", "POST").
        url : str
            URL to send the request to.
        **kwargs : dict
            Additional parameters to pass to the API request.
            
        Returns:
        --------
        Union[bytes, None]
            The API response content or None if the request fails.
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {Config.ELEVEN_API_KEY}"}
            
            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    return None

    async def find_voice_id_by_name(self, voice_name: str) -> str:
        """
        Find and return the voice ID corresponding to a given voice name.
        
        Parameters:
        -----------
        voice_name : str
            The name of the voice to search for.
            
        Returns:
        --------
        str
            The voice ID corresponding to the given voice name, or an empty string if not found.
        """
        voice_list, _ = await self.fetch_voice_list()
        for voice in voice_list:
            if voice["name"].lower() == voice_name.lower():
                return voice["voice_id"]
        return ""
    
    async def chat_gpt_voice(self, text: str, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
        """
        Get a response from the ChatGPT model for a given text input.
        
        Parameters:
        -----------
        text : str
            The text input to send to ChatGPT.
        user_id : int
            The user ID for context.
        context : ContextTypes.DEFAULT_TYPE
            Additional context for the ChatGPT model.
            
        Returns:
        --------
        str
            The text content of the ChatGPT response.
        """
        # Pass context to the function call
        response_data = await ChatGPT.get_chat_gpt_response(text, user_id, context)

        # Return chat GPT response
        return response_data['choices'][0]['message']['content']

    async def voice_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming voice messages, convert them to text, get a ChatGPT response, 
        and send back a voice message.
        
        Parameters:
        -----------
        update : Update
            Telegram update object containing the voice message.
        context : ContextTypes.DEFAULT_TYPE
            Additional context.
        """
        print("Voice message received.")
        user_name = update.effective_user.full_name
        try:
            voice_message = update.message.voice

            # Convert the voice message to text
            text = await self.convert_voice_to_text(voice_message, context.bot)

            # Get user ID
            user_id = update.effective_user.id

            # Pass context to the chat_gpt_voice function
            chat_gpt_response = await self.chat_gpt_voice(text, user_id, context)

            print(f"ChatGPT response: {chat_gpt_response}")

            # Retrieve the user's selected voice and mode
            user_id = update.effective_user.id
            voice_id = self.selected_voices.get(user_id, "7kRUX4UzUC1zcoeqNF4s")  # default voice if none selected
            print(f"[Debug] voice_message_handler: Voice ID selected for user {user_name} ({user_id}) is {voice_id}")
            mode = self.modes.get(user_id, "stable")  # default mode if none selected

            # Generate the voice message for the GPT response
            voice_message, error_message = await self.generate_voice_message(chat_gpt_response, voice_id, Config.ELEVEN_API_KEY, mode)

            if voice_message:
                with BytesIO(voice_message) as voice_io:
                    await send_chat_action_async(update, 'record_audio')
                    await update.message.reply_voice(voice=voice_io)
                    print("Voice message sent.")
            else:
                await send_chat_action_async(update, 'typing')
                await asyncio.sleep(0.5)
                await update.message.reply_text(error_message)
        except Exception as e:
            print(f"An error occurred in voice_message_handler: {e}")
            await send_chat_action_async(update, 'typing')
            await asyncio.sleep(0.5)
            await update.message.reply_text("An error occurred while processing the voice message. Please try again later.")

    async def generate_voice_message(self, text, voice_id, api_key, mode=None, language='en'):
        """
        Generate a voice message based on given text input.
        
        Parameters:
        -----------
        text : str
            The text to be converted into a voice message.
        voice_id : str
            The ID of the voice to use.
        api_key : str
            API key for the voice generation service.
        mode : str, optional
            The mode for voice generation (e.g., "stable", "unstable").
        language : str, optional
            The language of the text.
            
        Returns:
        --------
        Tuple[bytes, str]
            The generated voice message and any error messages.
        """
        try:
            if mode == "stable":
                stability = 0.6
                similarity_boost = 1
            elif mode == "unstable":
                stability = 0.1
                similarity_boost = 0.1
            else:
                stability = 0.5
                similarity_boost = 1

            # Use the multilingual model for complete lanuage support
            model_id = 'eleven_multilingual_v1'

            async with aiohttp.ClientSession() as session:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": api_key,
                }
                data = {
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost
                    },
                }
            
                # print(f"Debug Info:")
                # print(f"  Voice ID: {voice_id}")
                # print(f"  Text: {text}")
                # print(f"  Mode: {mode}")
                # print(f"  Stability: {stability}")
                # print(f"  Similarity Boost: {similarity_boost}")

                # print(f"Generating voice message for text: {text}")  # Debug line
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        voice_message = await response.read()
                        return voice_message, None
                    else:
                        error_message = f"Error generating voice message: {response.status}"
                        print(error_message)

                        # Print the response body for debugging
                        error_body = await response.text()
                        print(f"Error body: {error_body}")

                        return None, error_message
        except Exception as e:
            error_message = f"An error occurred while generating the voice message: {e}"
            print(error_message)
            return None, error_message

    async def download_voice_message_bytes(self, voice_message, bot):
        """
        Download the voice message and return it as bytes.
        
        Parameters:
        -----------
        voice_message : Voice Message Object
            The voice message to download.
        bot : Bot Object
            The bot instance to use for downloading the message.
            
        Returns:
        --------
        bytes
            The voice message in byte format.
        """
        try:
            file = await bot.getFile(voice_message.file_id)
            audio_data = await file.download_as_bytearray()
            return audio_data
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading voice message: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    async def audio_data_from_voice_bytes(self, bot, voice_message):
        """
        Convert voice message bytes into audio data suitable for further processing.
        
        Parameters:
        -----------
        bot : Bot Object
            The bot instance used for downloading the message.
        voice_message : Voice Message Object
            The voice message to convert.
            
        Returns:
        --------
        Audio Data
            The processed audio data.
        """
        try:
            audio_bytes = await self.download_voice_message_bytes(voice_message, bot)

            # Convert audio to WAV format using PyDub
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="ogg")
            wav_audio_bytes = io.BytesIO()
            audio_segment.export(wav_audio_bytes, format="wav")
            wav_audio_bytes.seek(0)

            # Using SpeechRecognition, recognize the audio and get the text
            with sr.AudioFile(wav_audio_bytes) as audio_source:
                recognizer = sr.Recognizer()
                audio_data = recognizer.record(audio_source)

            return audio_data
        except Exception as e:
            print(f"An error occurred while converting voice to text: {e}")
            return None

    async def convert_voice_to_text(self, voice_message, bot) -> str:
        """
        Convert a voice message to text using Deepgram API.
        
        Parameters:
        -----------
        voice_message : Voice Message Object
            The voice message to convert.
        bot : Bot Object
            The bot instance to use for downloading the message.
            
        Returns:
        --------
        str
            The transcribed text.
        """
        try:
            # Convert the voice message to audio data
            audio_data = await self.audio_data_from_voice_bytes(bot, voice_message)

            # Save audio_data as a temporary file (Deepgram requires a file-like object)
            with tempfile.NamedTemporaryFile() as temp_audio_file:
                wav_audio_bytes = audio_data.get_wav_data(convert_rate=16000)
                temp_audio_file.write(wav_audio_bytes)
                temp_audio_file.flush()

                # Open the temporary file and transcribe it using Deepgram asynchronously
                with open(temp_audio_file.name, 'rb') as audio_file:
                    # print(f"Sending {len(wav_audio_bytes)} bytes of WAV data for transcription")
                    source = {'buffer': audio_file, 'mimetype': 'audio/wav'}
                    response = await asyncio.create_task(
                        deepgram.transcription.prerecorded(
                            source,
                            {'smart_format': True,
                            'model': 'nova',
                            }
                        )
                    )

            # print(f"Deepgram response: {response}")

            text = response.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '').strip()

            print(f"Transcribed text: {text}")

            return text
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(error_message)
            return ""
        
    async def handle_v_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_gpt_response: str) -> None:
        user_id = update.effective_user.id
        mode = self.modes.get(user_id)
        voice_id = self.selected_voices.get(user_id, "7kRUX4UzUC1zcoeqNF4s")

        voice_message, error_message = await self.generate_voice_message(chat_gpt_response, voice_id, Config.ELEVEN_API_KEY, mode)

        if voice_message:
            with BytesIO(voice_message) as voice_io:
                await send_chat_action_async(update, 'record_audio')
                await update.message.reply_voice(voice=voice_io)
        else:
            await send_chat_action_async(update, 'typing')
            await asyncio.sleep(0.5)
            await update.message.reply_text("Sorry, there was a problem generating the voice message.")

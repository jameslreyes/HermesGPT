import aiohttp
import json
from config import Config
import requests

class FeedbackHandler():
    def __init__(self):
        pass

    async def store_feedback(user_name, feedback_text):
        try:
            # Download the existing feedback.txt file from Dropbox
            url = "https://content.dropboxapi.com/2/files/download"
            headers = {
                "Authorization": f"Bearer {Config.DROPBOX_ACCESS_TOKEN}",
                "Dropbox-API-Arg": json.dumps({"path": "/Apps/TelegramGPT/feedback.txt"}),
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    if status == 200:
                        existing_feedback = await response.text()
                    else:
                        existing_feedback = ""

            # Append the new feedback to the existing feedback
            feedback = existing_feedback + f"\nUser: {user_name}\nFeedback: {feedback_text}\n"

            # Upload the updated feedback.txt file to Dropbox
            headers["Dropbox-API-Arg"] = json.dumps({"path": "/Apps/TelegramGPT/feedback.txt", "mode": "overwrite"})
            url = "https://content.dropboxapi.com/2/files/upload"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=feedback.encode("utf-8")) as response:
                    if response.status != 200:
                        print(f"Error uploading feedback.txt. Status: {response.status}, Message: {await response.text()}")
                    else:
                        print("Feedback successfully uploaded.")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error uploading feedback.txt: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

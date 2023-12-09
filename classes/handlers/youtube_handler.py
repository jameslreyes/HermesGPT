from urllib.parse import urlparse
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeHandler():
    def __init__(self):
        pass

    async def convert_to_desktop_link(url):
        """
        Converts a YouTube mobile link to a desktop link.

        Args:
            url (str): The YouTube mobile link to be converted.

        Returns:
            str: The converted desktop link if the input is a mobile link, otherwise returns the input URL as is.

        Raises:
            None

        """
        try:
            parsed_url = urlparse(url)
            if parsed_url.netloc == "youtu.be":
                video_id = parsed_url.path[1:]
                return f"https://www.youtube.com/watch?v={video_id}"
            else:
                return url  # return the url as is if it's not a mobile link
        except Exception as e:
            print(f"An error occurred while converting the link: {e}")
            return None

    async def get_caption_text(video_id):
        """
        Retrieves the caption text for a YouTube video.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            str: The caption text of the video, or None if an error occurred.
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_generated_transcript(language_codes=['en'])
            
            if transcript:
                caption_text = ""
                for line in transcript.fetch():
                    caption_text += line["text"] + " "
                
                return caption_text
            
            return None
        except Exception as e:
            print(f"An error occurred while getting the caption text: {e}")
            return None
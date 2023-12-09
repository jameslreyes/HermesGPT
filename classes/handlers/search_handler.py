import traceback
import asyncio
import requests
import logging
import aiohttp
from bs4 import BeautifulSoup
from config import Config
import tiktoken
from telegram import Update
from telegram.ext import ContextTypes
from classes.chat_gpt import ChatGPT
from scripts.helper_functions import send_chat_action_async

logging.basicConfig(level=logging.INFO)

class SearchHandler():
    def __init__(self):
        pass

    @staticmethod
    def count_tokens(text: str) -> int:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        return len(tokens)

    async def bing_search(self, query, subscription_key):
        """
        Perform a Bing search using the given query and subscription key.

        Args:
            query (str): The search query.
            subscription_key (str): The Bing API subscription key.

        Returns:
            list: A list of dictionaries containing search results. Each dictionary has the following keys:
                - "title": The title of the search result.
                - "link": The URL of the search result.
                - "snippet": A snippet of the search result.

        Raises:
            Exception: If an error occurs during the search.

        """
        try:
            search_url = f'https://api.bing.microsoft.com/v7.0/search?q={query}'
            headers = {'Ocp-Apim-Subscription-Key': subscription_key}
            response = requests.get(search_url, headers=headers)
            data = response.json()
            search_results = []

            if 'webPages' in data:
                for result in data['webPages']['value']:
                    search_results.append({
                        "title": result['name'],
                        "link": result['url'],
                        "snippet": result['snippet']
                    })
            return search_results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    async def fetch_url_content(self, url: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')

                        # Remove unnecessary elements, such as scripts and styles
                        for script in soup(["script", "style"]):
                            script.decompose()

                        # Extract the text from the cleaned HTML
                        content = soup.get_text(separator="\n")

                        return content
                    else:
                        return ""
        except Exception as e:
            print(f"ERROR: /classes/handlers/search_handler.py/`SearchHandler().fetch_url_content`: Error fetching URL content from {url}. Status: {response.status}, Reason: {response.reason}")
            return ""

    async def handle_search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> None:
        user_id = update.message.from_user.id        
        search_results = await self.bing_search(query, Config.BING_API_KEY)
        MAX_RESULTS = 3  # Fetch content of top 3 search results
        MAX_TOKENS = 11000

        print(f"\n\nQuery: {query}")
        print(f"\n\nSearch results: {search_results}")

        try:
            if search_results:
                content_list = []
                total_token_count = 0

                # Limit our loop to the top MAX_RESULTS results
                for idx, result in enumerate(search_results[:MAX_RESULTS]):
                    url_content = await self.fetch_url_content(result["link"])
                    token_count = SearchHandler.count_tokens(url_content)
                    
                    # Log the Bing result for debugging or analysis
                    logging.info(f"Result {idx + 1}: Title: {result['title']}, Link: {result['link']}")

                    if total_token_count + token_count <= 16385:
                        content_list.append(url_content)
                        total_token_count += token_count
                    else:
                        break

                combined_content = "\n\n".join(content_list)
                print(f"\n\nCombined content: {combined_content}")

                if self.count_tokens(combined_content) > MAX_TOKENS:
                    trimmed_content = ""
                    for content in content_list:
                        if self.count_tokens(trimmed_content + content) <= MAX_TOKENS:
                            trimmed_content += content + "\n\n"
                    combined_content = trimmed_content

                print(f"\n\nCombined content after trimming: {combined_content}")

                # Clear the conversation history for the user
                if 'messages' in context.user_data and user_id in context.user_data['messages']:
                    context.user_data['messages'][user_id] = []

                # User-friendly prompt to guide GPT
                gpt_prompt = f"Tell me about '{query}'. Respond in a way that is easy to understand and that flows naturally. It should feel like a human is responding. Do not use bullet points or numbered lists. Respond only in paragraph form."
                print(f"\n\nPrompt: {gpt_prompt}")

                # Send "Thinking..." and store the message_id
                await send_chat_action_async(update, 'typing')
                thinking_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Searching for {query}...")
                thinking_message_id = thinking_message.message_id

                # Pass the combined content and prompt to ChatGPT and generate a response
                chat_gpt = ChatGPT()
                chat_gpt_response = await chat_gpt.get_chat_gpt_response(gpt_prompt + "\n\n" + combined_content, user_id, context, model="gpt-3.5-turbo-16k")

                formatted_response = chat_gpt_response["choices"][0]["message"]["content"]
                print(f"\n\nResponse: {formatted_response}")

                try:
                    # Try to edit the "Thinking..." message
                    await send_chat_action_async(update, 'typing')
                    await asyncio.sleep(1)
                    await context.bot.edit_message_text(chat_id=update.effective_chat.id, 
                                                        message_id=thinking_message_id, 
                                                        text=formatted_response)
                    print("\n\nSuccessfully edited message.")
                except Exception as e:
                    # If an exception occurs, print it to the console
                    print(f"Failed to edit message: {e}")
            else:
                await update.message.reply_text("Sorry, I couldn't find any results for your query.")
        except Exception as e:
            error_details = traceback.format_exc()
            logging.error(f"ERROR: /classes/handlers/search_handler.py/`SearchHandler().handle_search_command`: {e}\n{error_details}")
            await update.message.reply_text("Sorry, an error occurred while processing your request.")
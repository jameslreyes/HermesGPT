import aiohttp
import json
from classes.dropbox import DropboxClient

async def refresh_access_token_async(refresh_token, client_id, client_secret):
    async with aiohttp.ClientSession() as session:
        url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }

        async with session.post(url, data=data) as response:
            result = await response.json()
            new_access_token = result.get("access_token")
            return new_access_token

async def load_allowed_user_ids_from_dropbox(dbx):
    try:
        res_data = await DropboxClient.dbx_files_download_async("/Apps/TelegramGPT/allowed_user_ids.json", dbx)
        if res_data:
            return list(json.loads(res_data))
        else:
            return []
    except Exception as e:
        print(f"Error downloading allowed_user_ids.json: {e}")
        return []

async def save_allowed_user_ids_to_dropbox(allowed_user_ids, dbx):
    try:
        data = json.dumps(allowed_user_ids)
        
        async with aiohttp.ClientSession() as session:
            url = f"https://content.dropboxapi.com/2/files/upload"
            headers = {
                "Authorization": f"Bearer {dbx._oauth2_access_token}",
                "Content-Type": "application/octet-stream",
                "Dropbox-API-Arg": json.dumps({"path": "/Apps/TelegramGPT/allowed_user_ids.json", "mode": "overwrite"}),
            }

            async with session.post(url, headers=headers, data=data.encode("utf-8")) as response:
                res_data = await response.text()
                if response.status != 200:
                    print(f"Error uploading allowed_user_ids.json. Status: {response.status}, Message: {res_data}")
                    
    except Exception as e:
        print(f"Error uploading allowed_user_ids.json: {e}")
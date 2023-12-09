import aiohttp
import json

class DropboxClient():
    def __init__(self):
        pass

    async def dbx_files_download_async(path, dbx):
        async with aiohttp.ClientSession() as session:
            url = f"https://content.dropboxapi.com/2/files/download"
            headers = {
                "Authorization": f"Bearer {dbx._oauth2_access_token}",
                "Dropbox-API-Arg": json.dumps({"path": path})
            }

            async with session.post(url, headers=headers) as response:
                res_data = await response.text()
                return res_data
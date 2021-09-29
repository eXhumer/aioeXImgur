# aioeXImgur - Asynchronous Python interface to Imgur services
# Copyright (C) 2021  eXhumer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from mimetypes import guess_type
from pathlib import Path

from aiohttp import ClientSession, FormData


class Imgur:
    api_base_url = "https://api.imgur.com"
    base_url = "https://imgur.com"
    client_id = "546c25a59c58ad7"

    def __init__(self) -> None:
        self.__session: ClientSession | None = None

    async def __aenter__(self):
        self.__session = ClientSession()
        await self.__session.__aenter__()
        return self

    async def __aexit__(self, *err):
        await self.__session.__aexit__(*err)
        self.__session = None

    async def generate_album(self):
        return await self.__session.post(
            f"{Imgur.api_base_url}/3/album",
            params={"client_id": Imgur.client_id},
            json={},
        )

    async def poll_upload_tickets(self, *tickets: str):
        return await self.__session.get(
            f"{Imgur.base_url}/upload/poll",
            params={
                "client_id": Imgur.client_id,
                "tickets[]": tickets,
            },
        )

    async def update_album_metadata(self, deletehash: str, **metadata: str):
        return await self.__session.post(
            f"{Imgur.api_base_url}/3/album/{deletehash}",
            params={"client_id", Imgur.client_id},
            json=metadata,
        )

    async def update_media_metadata(self, deletehash: str, **metadata: str):
        return await self.__session.post(
            f"{Imgur.api_base_url}/3/image/{deletehash}",
            params={"client_id", Imgur.client_id},
            json=metadata,
        )

    async def upload_media(self, media_path: Path):
        if not media_path.name.endswith(".mp4"):
            raise ValueError("Unsupported media type!")

        media_key = (
            "video"
            if media_path.name.endswith(".mp4")
            else "image"
        )
        media_content_type = guess_type(media_path.name)[0]
        form_data = FormData()
        form_data.add_field("name", media_path.name)
        form_data.add_field("type", "file")
        form_data.add_field(
            media_key,
            media_path.open(mode="rb"),
            filename=media_path.name,
            content_type=media_content_type,
        )

        return await self.__session.post(
            f"{Imgur.api_base_url}/3/image",
            data=form_data,
            params={"client_id", Imgur.client_id},
        )

    async def delete_album(self, deletehash: str):
        return await self.__session.delete(
            f"{Imgur.api_base_url}/3/album/{deletehash}",
            params={"client_id", Imgur.client_id},
        )

    async def delete_media(self, deletehash: str):
        return await self.__session.delete(
            f"{Imgur.api_base_url}/3/image/{deletehash}",
            params={"client_id", Imgur.client_id},
        )

    async def add_media_to_album(
        self,
        album_deletehash: str,
        media_deletehash: str,
    ):
        return await self.__session.post(
            f"{Imgur.api_base_url}/3/album/{album_deletehash}/add",
            params={"client_id", Imgur.client_id},
            json={"deletehashes": media_deletehash},
        )

    async def arrange_album(
        self,
        album_deletehash: str,
        cover_media_id: str,
        *media_deletehashes: str,
    ):
        return await self.__session.put(
            f"{Imgur.api_base_url}/3/album/{album_deletehash}",
            params={"client_id", Imgur.client_id},
            json={"cover": cover_media_id, "deletehashes": media_deletehashes},
        )

    async def check_captcha(
        self,
        total_upload: int,
        g_recaptcha_response: str | None = None,
    ):
        return await self.__session.post(
            f"{Imgur.api_base_url}/3/upload/checkcaptcha",
            params={"client_id": Imgur.client_id},
            json={
                "total_upload": total_upload,
                "g-recaptcha-response": g_recaptcha_response,
            },
        )

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

"""Asynchronous Python interface to Imgur services"""
from argparse import ArgumentParser, Namespace
from asyncio import (
    gather,
    run,
    set_event_loop_policy,
    WindowsSelectorEventLoopPolicy,
)
from os import name as os_name
from pathlib import Path
from pkg_resources import require

from .service import Imgur

__version__ = require(__package__)[0].version


async def __parse_args(args: Namespace):
    if args.action == "upload-new-album":
        async with Imgur() as imgur:
            album_res = await imgur.generate_album()

            if not (
                album_res.status == 200
                and (album_res_json := await album_res.json())["status"] == 200
                and album_res_json["success"] is True
            ):
                raise ValueError("Invalid response while creating new album!")

            album_data = (
                album_res_json["data"]["id"],
                album_res_json["data"]["deletehash"],
            )

            media_paths = [
                media_path
                for media_path
                in args.media_paths
                if media_path.is_file()
            ]

            await imgur.check_captcha(len(media_paths))

            album_media_uploads = await gather(*[
                imgur.upload_media(media_path)
                for media_path
                in media_paths
            ])

            upload_tickets = []

            for res in album_media_uploads:
                if not (
                    res.status == 200
                    and (res_json := await res.json())["status"] == 200
                    and res_json["success"] is True
                ):
                    raise ValueError(
                        "\n".join([
                            "Invalid response while uploading media!",
                            await res.text(),
                        ]),
                    )

                upload_tickets.append(res_json["data"]["ticket"])

            media_datas = []

            while len(upload_tickets) != 0:
                res = await imgur.poll_upload_tickets(*upload_tickets)

                if not (
                    res.status == 200
                    and (res_json := await res.json())["status"] == 200
                    and res_json["success"] is True
                ):
                    raise ValueError(
                        "Invalid response while polling upload tickets",
                    )

                for ticket in upload_tickets:
                    if ticket in res_json["data"]["done"]:
                        upload_tickets.remove(ticket)
                        media_datas.append((
                            media_id := res_json["data"]["done"][ticket],
                            res_json["data"]["images"][media_id]["deletehash"]
                        ))

                continue

            await gather(*[
               imgur.add_media_to_album(album_data[1], media_data[1])
               for media_data
               in media_datas
            ])

            await imgur.arrange_album(
                album_data[1],
                media_datas[0][0],
                *[media_data[1] for media_data in media_datas],
            )

            print(f"Album ID: {album_data[0]}")


def console_main():
    if os_name == "nt":
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    parser = ArgumentParser()
    action_subparser = parser.add_subparsers(dest="action")
    upload_new_album_parser = action_subparser.add_parser("upload-new-album")
    upload_new_album_parser.add_argument(
        "media_paths",
        type=Path,
        nargs="*",
        metavar="MEDIA-PATH",
    )

    run(__parse_args(parser.parse_args()))

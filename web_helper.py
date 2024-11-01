import os
import random
import re
from typing import Optional
from bs4 import BeautifulSoup, Tag
from loguru import logger
import requests
from player_backends.player_backend import SongMetadata
from requests_html import HTMLSession


class WebHelper:
    def get_msm_url(self, song_metadata: SongMetadata) -> str:
        return f'https://modsamplemaster.thegang.nu/module.php?sha1={song_metadata.get("sha1")}'

    def download_module(
        self, module_id: str, temp_dir
    ) -> Optional[dict[str, Optional[str]]]:
        filename: Optional[str] = None
        module_link: Optional[str] = None

        url: str = f"https://api.modarchive.org/downloads.php?moduleid={module_id}"
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        if response.status_code == 200:
            module_filename: str = response.headers.get(
                "content-disposition", f"{module_id}.mod"
            ).split("filename=")[-1]
            module_link = f"https://modarchive.org/module.php?{module_id}"

            temp_file_path: str = f"{temp_dir}/{module_filename}"
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(response.content)
            filename = temp_file_path
            logger.debug(f"Module downloaded to: {filename}")
        return {"filename": filename, "module_link": module_link}

    def download_random_module(self, temp_dir) -> Optional[dict[str, Optional[str]]]:
        logger.debug("Getting a random module")

        url: str = "https://modarchive.org/index.php?request=view_player&query=random"
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("a", href=True, string=True, class_="standard-link")
        link_tag: Optional[Tag] = result if isinstance(result, Tag) else None
        if not link_tag:
            raise Exception("No module link found in the HTML response.")

        if isinstance(link_tag, Tag):
            href = link_tag["href"]
            module_url: str = href[0] if isinstance(href, list) else href
            if isinstance(module_url, list):
                module_url = module_url[0]
            if isinstance(module_url, str):
                module_id: str = module_url.split("=")[-1].split("#")[0]
                return self.download_module(module_id, temp_dir)
        return None

    def download_favorite_module(
        self, member_id, temp_dir
    ) -> Optional[dict[str, Optional[str]]]:
        filename: Optional[str] = None
        module_link: Optional[str] = None

        if member_id:
            logger.debug(f"Getting a random module for member ID: {member_id}")

            # Get the member's favorite modules list (links to the modules)
            url: str = (
                f"https://modarchive.org/index.php?request=view_member_favourites_text&query={member_id}"
            )

            response: requests.Response = requests.get(url)
            response.raise_for_status()

            soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
            result = soup.find("textarea")

            if result:
                favorite_modules: str = result.text
                module_links = favorite_modules.split("\n")

                # Remove modules with names already in the temp directory
                module_links = [
                    link
                    for link in module_links
                    if not os.path.exists(f"{temp_dir}/{link.split('#')[-1]}")
                ]

                if module_links:
                    # Pick a random module from the resulting list
                    module_url: str = random.choice(module_links)
                    module_id_and_name: str = module_url.split("=")[-1]
                    module_id: str = module_id_and_name.split("#")[0]

                    module = self.download_module(module_id, temp_dir)
                    if module:
                        filename, module_link = (
                            module["filename"],
                            module["module_link"],
                        )
                else:
                    logger.error("No new module links found in the member's favorites")
        else:
            logger.error("Member ID is empty")
        return {"filename": filename, "module_link": module_link}

    def download_author_module(
        self, author: str, temp_dir
    ) -> Optional[dict[str, Optional[str]]]:
        filename: Optional[str] = None
        module_link: Optional[str] = None

        if author:
            logger.debug(f"Getting a random module by author: {author}")

            url: str = (
                f"https://modarchive.org/index.php?request=search&search_type=guessed_artist&query={author}"
            )

            response: requests.Response = requests.get(url)
            response.raise_for_status()

            soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

            # Get pagination number
            pagination = soup.find("select", class_="pagination")
            if pagination:
                if isinstance(pagination, Tag):
                    options = pagination.find_all("option")
                    if options:
                        last_page = int(options[-1].text)

                        # Get a random page number
                        page_number = random.randint(1, last_page)

                        # Get the page with the random number
                        url = f"{url}&page={page_number}#mods"

                        response = requests.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.content, "html.parser")

                        # Get all a tags with title "Download"
                        download_links = soup.find_all("a", title="Download")
                        if download_links:
                            download_link = random.choice(download_links)
                            module_id = (
                                download_link["href"].split("=")[-1].split("#")[0]
                            )
                            module = self.download_module(module_id, temp_dir)
                            if module:
                                filename, module_link = (
                                    module["filename"],
                                    module["module_link"],
                                )
                        else:
                            logger.error("No download links found on the page")
                    else:
                        logger.error("No pagination options found")
                else:
                    logger.error("No pagination tag found")
            else:
                logger.error("No pagination found")
        else:
            logger.error("Author is empty")

        return {"filename": filename, "module_link": module_link}

    def lookup_modarchive_mod_url(self, song_metadata: SongMetadata) -> str:
        filename = song_metadata.get("filename")
        url = f"https://modarchive.org/index.php?request=search&query={filename}&submit=Find&search_type=filename"

        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            result = soup.find("a", string=filename)

            if result and isinstance(result, Tag):
                href = result["href"]
                if isinstance(href, list):
                    href = href[0]
                return "https://modarchive.org/" + href
        return ""

    def lookup_modarchive_mod_artist(
        self, song_metadata: SongMetadata
    ) -> dict[str, str]:
        logger.debug("Looking up artist on ModArchive")

        url: str = self.lookup_modarchive_mod_url(song_metadata)

        result_dict: dict[str, str] = {}

        if url:
            session = HTMLSession()

            r = session.get(url)

            r.html.render()

            result = r.html.find("div.mod-page-archive-info")
            if result:
                # Check for registered artist
                artist_links = result[0].find("a.standard-link")

                if len(artist_links) == 0:
                    logger.debug("No artist links found")

                for artist_link in artist_links:
                    href = artist_link.attrs["href"]
                    if href.startswith("member"):
                        result_dict["registered_artist"] = artist_link.text
                        logger.debug(f"Registered artist: {artist_link.text}")
                    elif href.startswith("index"):
                        result_dict["guessed_artist"] = artist_link.text
                        logger.debug(f"Guessed artist: {artist_link.text}")
        return result_dict

    def lookup_msm_mod_url(self, song_metadata: SongMetadata) -> str:
        url: Optional[str] = None
        if song_metadata:
            url = self.get_msm_url(song_metadata)
        if url:
            # Check if the link returns a 404
            response = requests.get(url)
            if response.status_code == 200:
                return url
        return ""

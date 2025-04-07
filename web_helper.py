import random
from typing import Optional, List
from bs4 import BeautifulSoup, Tag
from loguru import logger
import requests
from player_backends.Song import Song


class WebHelper:
    def get_msm_url(self, song: Song) -> str:
        return f"https://modsamplemaster.thegang.nu/module.php?sha1={song.sha1}"

    def download_module_file(self, module_id: int, temp_dir: str) -> Optional[str]:
        filename: Optional[str] = None
        # module_link: Optional[str] = None

        url: str = f"https://api.modarchive.org/downloads.php?moduleid={module_id}"
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        if response.status_code == 200:
            module_filename: str = response.headers.get(
                "content-disposition", f"{module_id}.mod"
            ).split("filename=")[-1]
            # module_link = f"https://modarchive.org/module.php?{module_id}"

            temp_file_path: str = f"{temp_dir}/{module_filename}"
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(response.content)
            filename = temp_file_path
            logger.info(f"Module downloaded to: {filename}")
        else:
            logger.error(f"Failed to download module with ID: {module_id}")
        return filename

    def get_random_module_id(self) -> Optional[int]:
        url: str = "https://modarchive.org/index.php?request=view_player&query=random"
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("a", href=True, string=True, class_="standard-link")
        link_tag: Optional[Tag] = result if isinstance(result, Tag) else None
        if link_tag:
            href = link_tag["href"]
            module_url: str = href[0] if isinstance(href, list) else href
            if isinstance(module_url, list):
                module_url = module_url[0]
            if isinstance(module_url, str):
                module_id: str = module_url.split("=")[-1].split("#")[0]
                return int(module_id)
        return None

    def get_member_module_url_list(self, member_id: int) -> List[str]:
        url: str = (
            f"https://modarchive.org/index.php?request=view_member_favourites_text&query={member_id}"
        )

        response: requests.Response = requests.get(url)
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")
        result = soup.find("textarea")

        if result:
            favorite_modules: str = result.text
            return favorite_modules.split("\n")
        return []

    def get_member_module_id_list(self, member_id: int) -> List[int]:
        module_urls = self.get_member_module_url_list(member_id)

        ids: List[int] = []

        for module_url in module_urls:
            id_str = module_url.split("moduleid=")[-1].split("#")[0]

            if id_str:
                module_id = int(id_str)
                ids.append(module_id)

        return ids

    def get_random_favorite_module_id(self, member_id: int) -> Optional[int]:
        module_ids = self.get_member_module_id_list(member_id)
        if module_ids:
            return random.choice(module_ids)
        return None

    def get_random_artist_module_id(self, artist: str) -> Optional[int]:
        url: str = (
            f"https://modarchive.org/index.php?request=search&search_type=guessed_artist&query={artist}"
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
                        module_id: str = (
                            download_link["href"].split("=")[-1].split("#")[0]
                        )
                        return int(module_id)
                    else:
                        logger.error("No download links found on the page")
                else:
                    logger.error("No pagination options found")
            else:
                logger.error("No pagination tag found")
        else:
            logger.error("No pagination found")
        return None

    def lookup_modarchive_mod_url(self, song: Song) -> str:
        logger.info(f"Looking up ModArchive URL for song: {song}")
        def search_modarchive(query: str, search_type: str) -> Optional[str]:
            url = f"https://modarchive.org/index.php?request=search&query={query}&submit=Find&search_type={search_type}"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                # Check if there are search results
                search_results_header = soup.find(
                    "h1", class_="site-wide-page-head-title", string="Search Results"
                )
                if search_results_header:
                    result = soup.find("a", class_="standard-link", href=True)
                    if result and isinstance(result, Tag):
                        href = result["href"]
                        if isinstance(href, list):
                            href = href[0]
                        return "https://modarchive.org/" + href
            return None

        filename = song.filename.split("/")[-1]
        url = search_modarchive(filename, "filename")
        if not url:
            if song.title and song.title != "<no songtitle>":
                title_with_plus = song.title.replace(" ", "+")
                url = search_modarchive(title_with_plus, "filename_or_songtitle")
        return url if url else ""

    def lookup_msm_mod_url(self, song: Song) -> str:
        url: Optional[str] = None
        if song:
            url = self.get_msm_url(song)
        if url:
            # Check if the link returns a 404
            response = requests.get(url)
            if response.status_code == 200:
                return url
        return ""

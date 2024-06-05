import os
import argparse
import requests
import questionary
import re
import time

from bs4 import BeautifulSoup
from urllib.parse import unquote
from typing import Optional, Tuple, Dict, List

from sources.vidplay import VidplayExtractor
from sources.filemoon import FilemoonExtractor
from utils import Utilities, VidSrcError, NoSourcesFound

SUPPORTED_SOURCES = ["Vidplay", "Filemoon"]

class VidSrcExtractor:
    BASE_URL = "https://vidsrc.to"
    DEFAULT_KEY = "WXrUARXb1aDLaZjI"
    PROVIDER_URL = "https://vidplay.online" # vidplay.site / vidplay.online / vidplay.lol
    TMDB_BASE_URL = "https://www.themoviedb.org"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

    def __init__(self, **kwargs) -> None:
        self.source_name = kwargs.get("source_name")
        self.fetch_subtitles = kwargs.get("fetch_subtitles")

    def decrypt_source_url(self, source_url: str) -> str:
        encoded = Utilities.decode_base64_url_safe(source_url)
        decoded = Utilities.decode_data(VidSrcExtractor.DEFAULT_KEY, encoded)
        decoded_text = decoded.decode('utf-8')

        return unquote(decoded_text)

    def get_source_url(self, source_id: str) -> str:
        req = requests.get(f"{VidSrcExtractor.BASE_URL}/ajax/embed/source/{source_id}")
        if req.status_code != 200:
            error_msg = f"Couldnt fetch {req.url}, status code: {req.status_code}..."
            raise VidSrcError(error_msg)

        data = req.json()
        encrypted_source_url = data.get("result", {}).get("url")
        return self.decrypt_source_url(encrypted_source_url)

    def get_sources(self, data_id: str) -> Dict:
        req = requests.get(f"{VidSrcExtractor.BASE_URL}/ajax/embed/episode/{data_id}/sources")
        if req.status_code != 200:
            error_msg = f"Couldnt fetch {req.url}, status code: {req.status_code}..."
            raise VidSrcError(error_msg)
        
        data = req.json()
        return {video.get("title"): video.get("id") for video in data.get("result")}

    def get_streams(self, media_type: str, media_id: str, season: Optional[str], episode: Optional[str]) -> Tuple[Optional[List], Optional[Dict], Optional[str]]:
        url = f"{VidSrcExtractor.BASE_URL}/embed/{media_type}/{media_id}"
        if season and episode:
            url += f"/{season}/{episode}"

        print(f"[>] Requesting {url}...")
        req = requests.get(url)
        if req.status_code != 200:
            print(f"[VidSrcExtractor] Couldnt fetch \"{req.url}\", status code: {req.status_code}\n[VidSrcExtractor] \"{self.source_name}\" likely doesnt have the requested media...")
            return None, None, None

        soup = BeautifulSoup(req.text, "html.parser")
        sources_code = soup.find('a', {'data-id': True})
        if not sources_code:
            print("[VidSrcExtractor] Could not fetch data-id, this could be due to an invalid imdb/tmdb code...")
            return None, None, None

        sources_code = sources_code.get("data-id")
        sources = self.get_sources(sources_code)
        source = sources.get(self.source_name)
        if not source:
            available_sources = ", ".join(list(sources.keys()))
            print(f"[VidSrcExtractor] No source found for \"{self.source_name}\"\nAvailable Sources: {available_sources}")
            return None, None, None

        source_url = self.get_source_url(source)

        if self.source_name == "Vidplay":
            print(f"[>] Fetching source for \"{self.source_name}\"...")

            extractor = VidplayExtractor()
            return extractor.resolve_source(url=source_url, fetch_subtitles=self.fetch_subtitles, provider_url=VidSrcExtractor.PROVIDER_URL)
        
        elif self.source_name == "Filemoon":
            print(f"[>] Fetching source for \"{self.source_name}\"...")

            if self.fetch_subtitles: 
                print(f"[VidSrcExtractor] \"{self.source_name}\" doesnt provide subtitles...")

            extractor = FilemoonExtractor()
            return extractor.resolve_source(url=source_url, fetch_subtitles=self.fetch_subtitles, provider_url=VidSrcExtractor.PROVIDER_URL)
        
        else:
            print(f"[VidSrcExtractor] Sorry, this doesnt currently support \"{self.source_name}\" :(\n[VidSrcExtractor] (if you create an issue and ask really nicely ill maybe look into reversing it though)...")
            return None, None, None
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vidsrc Command Line Interface")
    parser.add_argument("-src", "--source", dest="source_name", choices=SUPPORTED_SOURCES,
                        help="Specify the source name") 
    parser.add_argument("-id", "--media-id", dest="media_id", type=str,
                        help="Specify tmdb/imdb code to watch")
    parser.add_argument("-se", "--season", dest="season", type=str,
                        help="Specify the season number")
    parser.add_argument("-ep", "--episode", dest="episode", type=str,
                        help="Specify the episode number")
    parser.add_argument("-endep", "--end-episode", dest="end_episode", type=str,
                        help="Specify the end episode number")
    parser.add_argument("-cid", "--custom-id", dest="custom_id", type=str,
                        help="Specify a custom name for the media id")
    args = parser.parse_args()

    source_name = args.source_name or questionary.select("Select Source", choices=SUPPORTED_SOURCES).unsafe_ask()

    if source_name == "Filemoon": # This source doesnt provide subtitles as of 31/12/2023
        fetch_subtitles = False
    else:
        fetch_subtitles = True

    vse = VidSrcExtractor(
        source_name = source_name,
        fetch_subtitles = fetch_subtitles,
    )

    media_id = args.media_id
    media_type = "tv"
    custom_id = args.custom_id

    if not media_id:
        media_id = questionary.text("Input imdb/tmdb code").unsafe_ask()

    if not custom_id:
        custom_id = questionary.text("Enter a custom name: ").unsafe_ask()

    se = args.season or questionary.text("Input Season Number").unsafe_ask()
    ep = args.episode or int(questionary.text("Input Start Episode Number").unsafe_ask()) 
    end_ep = args.end_episode or int(questionary.text("Input Finish Episode Number").unsafe_ask()) 

    if media_type == "tv":
        
        for episode_number in range(int(ep), int(end_ep) + 1):
            sub_link = None
            streams, subtitles, source_url = vse.get_streams(media_type, media_id, se, str(episode_number))
            index, fetch_attempts = (SUPPORTED_SOURCES.index(vse.source_name), 0)

            while not streams:
                index += 1 # we want the first source after the current index
                fetch_attempts += 1
                time.sleep(5)

                if (fetch_attempts > 1) and (not streams):
                    print("No sources were found.")
                    break  

                streams, subtitles, source_url = vse.get_streams(media_type, media_id, se, str(episode_number))

            if not streams:
                continue
            
            stream = questionary.select("Select Stream", choices=streams).unsafe_ask() if len(streams) > 1 else streams[0]

            if subtitles:
                subtitle_list = list(subtitles.keys())
                subtitle_list.append("None")
                selection = "English"
                sub_link = subtitles.get(selection)
            
            # Define the regex pattern to match the number prefix and date
            pattern = r"^\d+\.\s+|\(\d{1,2}\.\s+\w+\s+\d{4}\)$"

            if custom_id:
                cleaned_text = custom_id.strip().replace(" ", ".")
            else:
                cleaned_text = media_id

            se = int(se)
            filename = f"{cleaned_text}.S{se:02d}E{episode_number:02d}"

            tv_dir = "TV"
            os.makedirs(tv_dir, exist_ok=True)
            series_dir = os.path.join(tv_dir, cleaned_text)
            os.makedirs(series_dir, exist_ok=True)
            season_dir = os.path.join(series_dir, f"S{se:02d}")
            os.makedirs(season_dir, exist_ok=True)

            filepath = os.path.join(season_dir, filename)

            print("[>]")
            print("[>] Downloading: " + filename)
            print("[>] Stream selected: " + stream)
            print("[>] Subtitle link: " + sub_link) if sub_link is not None else print("[>] Subtitle link: None")
            print("[>]")

            os.system(f"yt-dlp {stream} -N 4 -R 20 -o {filepath}.mp4")
            try:
                if sub_link is not None:
                    response = requests.get(sub_link)
                    subs_dir = os.path.join(season_dir, "Subs")
                    os.makedirs(subs_dir, exist_ok=True)
                    subpath = os.path.join(subs_dir, filename)
                    with open(f"{subpath}.vtt", 'wb') as file:
                        file.write(response.content)

                    os.system(f"vtt_to_srt {subpath}.vtt")
                    if os.path.exists(f"{subpath}.vtt"): os.remove(f"{subpath}.vtt")
                    if os.path.exists(f"{subpath}.srt"):
                        print(f"[>] Downloaded {subpath}.srt")
            except:
                pass

            if os.path.exists(f"{filepath}.mp4"):
                print(f"[>] Downloaded {filepath}.mp4")
            

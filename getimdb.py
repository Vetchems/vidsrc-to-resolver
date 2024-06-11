import json
import re
import requests
from bs4 import BeautifulSoup
import PyMovieDb
import argparse
import os
import questionary

SUPPORTED_SOURCES = ["Vidplay", "Filemoon"]

parser = argparse.ArgumentParser(description="Vidsrc Command Line Interface")
parser.add_argument("-src", "--source", dest="source_name", choices=SUPPORTED_SOURCES,
                    help="Specify the source name")
parser.add_argument("-id", "--media-id", dest="media_id", type=str,
                    help="Specify IMDb code to generate commands for.")
parser.add_argument("-silent", "--silent", dest="silent", action="store_true", help="Silent mode")
parser.add_argument("-dl", "--auto-download", dest="auto_dl", action="store_true", help="Auto Download mode")
parser.add_argument("-f", "--input-file", dest="input_file", type=str, help="Input file with list of IMDb codes or links")
args = parser.parse_args()

def remove_bad_filename_characters(filename):
    """
    Removes characters from the filename that are not allowed in Windows filenames.
    """
    bad_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in bad_characters:
        filename = filename.replace(char, "")
    return filename

def fetch_title_from_imdb(imdb_id):
    """
    Fetch the title of a series or movie from IMDb using web scraping.
    """
    url = f"https://www.imdb.com/title/{imdb_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 403:
        raise Exception("403 Forbidden: IMDb is blocking the request.")
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('title').text.split(' - IMDb')[0]  # Extract title from the page's <title> tag
    is_series = True if "Series" in title else False
    if is_series:
        title = re.sub(r'\s*\(.*?\)\s*', '', title)  # Remove content in parentheses
    return title, is_series

def extract_imdb_id(link_or_id):
    """
    Extract the IMDb ID from a given link or return it if it's already an ID.
    """
    imdb_id_pattern = r'tt\d{7,8}'
    match = re.search(imdb_id_pattern, link_or_id)
    if match:
        return match.group(0)
    else:
        raise ValueError(f"Invalid IMDb ID or link: {link_or_id}")

def process_imdb_id(ttid, source_name, auto_dl, silent):
    """
    Process a single IMDb ID to fetch its details and create a batch file.
    """
    imdb = PyMovieDb.IMDB()
    
    print(f"Fetching from IMDb website for ID: {ttid}...")
    media_name, is_series = fetch_title_from_imdb(ttid)
    if media_name == '404 Error':
        print("404 Error: Series not found. Please check IMDb code or continue with manual input.")
        media_name = ''
    if not media_name:
        media_name = questionary.text("Failed to fetch title. Enter series name (q to quit): ").unsafe_ask()
        if media_name == 'q':
            return

    cleaned_media_name = remove_bad_filename_characters(media_name)
    print(f'Name: {media_name}\nCleaned name: {cleaned_media_name}')

    media_type = "TV Series" if is_series else "Movie"
    print(f"Media type: {media_type}")

    if is_series:
        episodes = json.loads(imdb.get_episodes(ttid))
        season_count = episodes['season_count']
        print(f"Total seasons: {season_count}")

        batch_filename = f"{cleaned_media_name.replace(' ', '.')}_{ttid}_{source_name}_{season_count}_Seasons.bat"
        with open(batch_filename, "w") as f:
            f.write("@echo off\n")
            for season in episodes['seasons']:
                season_id = season['id']
                episode_count = season['episode_count']
                print(f"Season {season_id} has {episode_count} episodes")
                if season_id == "Unknown":
                    continue
                f.write(f'python downstream.py -src "{source_name}" -id "{ttid}" -se {season_id} -ep 1 -endep {episode_count} -cid "{cleaned_media_name}" -type "tv"\n')
    else:
        batch_filename = f"{cleaned_media_name.replace(' ', '.').replace('(', '').replace(')', '')}_{ttid}_{source_name}.bat"
        with open(batch_filename, "w") as f:
            f.write("@echo off\n")
            f.write(f'python downstream.py -src "{source_name}" -id "{ttid}" -cid "{cleaned_media_name}" -type "movie"\n')

    print(f"[>] Batch File has been written to {batch_filename}")
    if auto_dl:
        print("[>] Starting download...")
        os.system(f"{batch_filename}")
        return

    if not silent:
        if questionary.confirm("Would you like to download the batch file?").unsafe_ask():
            if questionary.confirm("Would you like to open a new window for the download?").unsafe_ask():
                os.system(f"start {batch_filename}")
            else:
                os.system(f"{batch_filename}")

auto_dl = args.auto_dl if args.auto_dl else False

if auto_dl:
    source_name = args.source_name or "Vidplay"
else:
    source_name = args.source_name or questionary.select("Select Source", choices=SUPPORTED_SOURCES).unsafe_ask()

# Main logic to handle input file or single media ID
if args.input_file:
    with open(args.input_file, "r") as file:
        imdb_ids_or_links = [line.strip() for line in file.readlines()]
    for item in imdb_ids_or_links:
        try:
            imdb_id = extract_imdb_id(item)
            process_imdb_id(imdb_id, source_name, auto_dl, args.silent)
        except ValueError as e:
            print(e)
else:
    ttid = args.media_id if args.media_id else questionary.text("Enter IMDb code: ").unsafe_ask()
    ttid = extract_imdb_id(ttid)
    process_imdb_id(ttid, source_name, auto_dl, args.silent)

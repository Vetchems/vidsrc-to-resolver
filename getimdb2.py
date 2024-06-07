import json
import re
import requests
from bs4 import BeautifulSoup
import PyMovieDb
import argparse
import os
import questionary

parser = argparse.ArgumentParser(description="Vidsrc Command Line Interface")
parser.add_argument("-id", "--media-id", dest="media_id", type=str,
                    help="Specify IMDb code to generate commands for.")
args = parser.parse_args()

def remove_bad_filename_characters(filename):
    """
    Removes characters from the filename that are not allowed in Windows filenames.

    Parameters:
    filename (str): The string from which to remove bad characters.

    Returns:
    str: The cleaned string with bad characters removed.
    """
    bad_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in bad_characters:
        filename = filename.replace(char, "")
    return filename

def fetch_title_from_imdb(imdb_id):
    """
    Fetch the title of a series or movie from IMDb using web scraping.

    Parameters:
    imdb_id (str): The IMDb ID of the series or movie.

    Returns:
    str: The title of the series or movie.
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
    title = re.sub(r'\s*\(.*?\)\s*', '', title)  # Remove content in parentheses
    return title

imdb = PyMovieDb.IMDB()

ttid = args.media_id if args.media_id else questionary.text("Enter IMDb code: ").unsafe_ask()
# raw_data = imdb.get_by_id(ttid)
# data = json.loads(raw_data)

# if 'name' in data:
#     series_name = data['name']
# else:
print("Series Data Not Found. Fetching from IMDb website...")
series_name = fetch_title_from_imdb(ttid)
if series_name == '404 Error':
    print("404 Error: Series not found. Please check IMDb code or continue with manual input.")
    series_name = ''
if not series_name:
    series_name = questionary.text("Failed to fetch title. Enter series name (q to quit): ").unsafe_ask()
    if series_name == 'q':
        exit()

cleaned_series_name = remove_bad_filename_characters(series_name)
print(f'Name: {series_name}\nCleaned name: {cleaned_series_name}')

episodes = json.loads(imdb.get_episodes(ttid))
season_count = episodes['season_count']
print(f"Total seasons: {season_count}")

batch_filename = f"{cleaned_series_name.replace(' ', '.')}_{ttid}_{season_count}_Seasons.bat"
with open(batch_filename, "w") as f:
    f.write("@echo off\n")
    for season in episodes['seasons']:
        season_id = season['id']
        episode_count = season['episode_count']
        print(f"Season {season_id} has {episode_count} episodes")
        if season_id == "Unknown":
            continue
        print(f'python tvrip-retry4.py -src "Vidplay" -id "{ttid}" -se {season_id} -ep 1 -endep {episode_count} -cid "{cleaned_series_name}"')
        f.write(f'python tvrip-retry4.py -src "Vidplay" -id "{ttid}" -se {season_id} -ep 1 -endep {episode_count} -cid "{cleaned_series_name}"\n')
print(f"[>] Batch File has been written to {batch_filename}")

if questionary.confirm("Would you like to download the batch file?").unsafe_ask():
    if questionary.confirm("Would you like to open a new window for the download?").unsafe_ask():
        os.system(f"start {batch_filename}")
    else:
        os.system(f"{batch_filename}")

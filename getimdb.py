import json
import PyMovieDb
import argparse
import os
import questionary

parser = argparse.ArgumentParser(description="Vidsrc Command Line Interface")
parser.add_argument("-id", "--media-id", dest="media_id", type=str,
                    help="Specify imdb code to generate commands for.")
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



imdb = PyMovieDb.IMDB()

ttid = args.media_id if args.media_id else questionary.text("Enter IMDB code: ").unsafe_ask()
raw_data = imdb.get_by_id(ttid)
# data = json.loads(imdb.get_by_id(ttid))
data = json.loads(raw_data)

episodes = json.loads(imdb.get_episodes(ttid))

series_name = data.get('name')
series_name = series_name if series_name else questionary.text("Series Data Not Found. Enter series name: ").unsafe_ask()
cleaned_series_name = remove_bad_filename_characters(series_name)
print(f'Name: {series_name}\nCleaned name: {cleaned_series_name}')
# Print the season count
season_count = episodes['season_count']
print(f"Total seasons: {season_count}")

with open(f"{cleaned_series_name.replace(' ', '.')}_{ttid}_{season_count}_Seasons.bat", "w") as f:
    f.write("@echo off\n")
    for season in episodes['seasons']:
        season_id = season['id']
        episode_count = season['episode_count']
        print(f"Season {season_id} has {episode_count} episodes")
        if season_id == "Unknown":
            continue
        print(f'python tvrip-retry3.py -src "Vidplay" -id "{ttid}" -se {season_id} -ep 1 -endep {episode_count} -cid "{cleaned_series_name}"')
        f.write(f'python tvrip-retry3.py -src "Vidplay" -id "{ttid}" -se {season_id} -ep 1 -endep {episode_count} -cid "{cleaned_series_name}"\n')
print(f"[>] Batch File has been written to {cleaned_series_name.replace(' ', '.')}_{ttid}_{season_count}_Seasons.bat")

if questionary.confirm("Would you like to download the batch file?").unsafe_ask():
    if questionary.confirm("Would you like to open a new window for the download?").unsafe_ask():
        os.system(f"start {cleaned_series_name.replace(' ', '.')}_{ttid}_{season_count}_Seasons.bat")
    else:
        os.system(f"{cleaned_series_name.replace(' ', '.')}_{ttid}_{season_count}_Seasons.bat")


    
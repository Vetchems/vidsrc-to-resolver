import requests
import questionary
from questionary import Choice, Separator
import os

# URLs to fetch data from
movie_url_template = "https://vidsrc.xyz/movies/latest/page-{}.json"
tvshow_url_template = "https://vidsrc.xyz/tvshows/latest/page-{}.json"

# Function to fetch data from the provided URL
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Will raise an error for bad responses
    return response.json()

# Function to create choices from fetched data
def create_choices(data, key):
    choices = [Choice(f"{item['title']} IMDb: {item['imdb_id']} https://www.imdb.com/title/{item['imdb_id']} ({item.get('quality', 'N/A')})", value=item) for item in data["result"]]
    return choices

# Function to prompt user with options
def prompt_user(choices, title, page, total_pages):
    return questionary.select(
        f"{title} - Page {page}/{total_pages}",
        choices=choices + [
            Separator(),
            Choice("Next Page", "next"),
            Choice("Previous Page", "prev"),
            Choice("Quit", "quit")
        ]
    ).ask()

# Main interactive function
def interactive_fetch(title, url_template):
    page = 1
    total_pages = None
    selected_items = []

    while True:
        data = fetch_data(url_template.format(page))
        total_pages = data.get("pages", total_pages)
        choices = create_choices(data, "title")

        # Prompt user
        choice = prompt_user(choices, title, page, total_pages)

        if choice == "next":
            if page < total_pages:
                page += 1
            else:
                questionary.print("You are on the last page.", style="bold red")
        elif choice == "prev":
            if page > 1:
                page -= 1
            else:
                questionary.print("You are on the first page.", style="bold red")
        elif choice == "quit":
            break
        else:
            selected_items.append(choice)

    return selected_items

content_choice = questionary.select(
    "What content do you want to browse?",
    choices=[
        Choice("Movies", value="movies"),
        Choice("TV Shows", value="tvshows")
    ]
).unsafe_ask()

# Fetch Movies and TV Shows
if content_choice == "movies":
    movies = interactive_fetch("Latest Movies", movie_url_template) or []
    print("Selected Movies:")
    for movie in movies:
        print(f"Title: {movie['title']}, IMDb ID: {movie['imdb_id']}, https://www.imdb.com/title/{movie['imdb_id']}, Quality: {movie.get('quality', 'N/A')}")
elif content_choice == "tvshows":
    tvshows = interactive_fetch("Latest TV Shows", tvshow_url_template) or []
    print("Selected TV Shows:")
    for tvshow in tvshows:
        print(f"Title: {tvshow['title']}, IMDb ID: {tvshow['imdb_id']}, https://www.imdb.com/title/{tvshow['imdb_id']}")
        os.system(f"python getimdb2.py -id {tvshow['imdb_id']} -silent")
else:
    print("Invalid choice. Exiting.")

    

print("Script completed.")

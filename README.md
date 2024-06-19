# Vidsrc.to Resolver/CLI
*A simple cli for fetching content from vidsrc.to by resolving m3u8's from common sources used by the site.*

---

### Fork Edits
- Download Functionality
- TV Show Whole Season Download
- TV Show Entire Series Download
- Movie Download

---

### Supports
- vidplay.site (https://vidplay.site/)
- filemoon (https://filemoon.sx/)

---

### Pre-requisites
- mpv-player (https://mpv.io/)
- python3 (https://www.python.org/)
- ffmpeg (https://www.ffmpeg.org/)
- yt-dlp (https://github.com/yt-dlp/yt-dlp)

---

### Installation
Download the repo

```git clone https://github.com/vetchems/vidsrc-to-resolver.git```

Move into repo folder

```cd vidsrc-to-resolver```

Download dependencies

```pip install -r requirements.txt```

Run the file

```python3 vidsrc.py```

---

### Usage

```python3 vidsrc.py --help```

---

### Fork Specific Examples

#### Download a batch of episodes from a season.

Download episodes from imdb id `"tt4396630"` season 1, starting with episode 1 and ending with episode 13.
If `-cid` is set then this name is used otherwise the imdb id is used.

```python downstream.py -src "Vidplay" -id "tt4396630" -se 1 -ep 1 -endep 13 -cid "The Gifted" -type "tv"```

#### Auto download entire TV Show/Movie

Download with prompt guides. You will be asked for IMDb id. The series name will attempt to be discovered and used but if not found you will be prompted to enter a name to use.

This creates a batch file of the commands to download the entire series. You will be prompted to download now and the batch file saved for later.

```python getimdb.py```

You can skip the imdb id prompt by specifying it in the command line. and auto download with -dl

```python getimdb.py -dl -id tt6257970```


### Note
This is purely intended as proof of concept, the distribution of program is intended for educational purposes ONLY. 

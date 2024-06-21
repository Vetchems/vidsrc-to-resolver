from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import threading
import time
from queue import Queue
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
CORS(app)

# Configuration
MAX_SIMULTANEOUS_TASKS = 4  # Configurable number of simultaneous tasks

# Task Management
task_queue = Queue()
running_tasks = {}
task_results = {}
progress = {}
poster_links = {}

def get_poster_link(imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            poster_div = soup.find('div', class_='ipc-media--poster-27x40')
            if poster_div:
                poster_img = poster_div.find('img')
                if poster_img:
                    return poster_img.get('src')
            else:
                return None
        else:
            print(f"Failed to fetch IMDb page for {imdb_id}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching IMDb page for {imdb_id}: {str(e)}")
        return None

def run_script(imdb_id, source_name, nix, task_id):
    start_time = time.time()
    command = f'python getimdb.py --media-id {imdb_id} --source {source_name}'
    command += ' --auto-download'
    command += ' --newline'
    
    if nix:
        command += ' --nix'

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in iter(process.stdout.readline, b''):
        progress[task_id] = line.decode().strip()

    process.stdout.close()
    process.wait()
    elapsed_time = time.time() - start_time
    progress[task_id] = f"Completed in {elapsed_time:.2f} seconds"
    task_results[task_id] = (progress[task_id], imdb_id, source_name)

    running_tasks.pop(task_id, None)
    process_next_task()

def process_next_task():
    while len(running_tasks) < MAX_SIMULTANEOUS_TASKS and not task_queue.empty():
        task_id, imdb_id, source_name, nix = task_queue.get()
        running_tasks[task_id] = {"start_time": time.time(), "imdb_id": imdb_id, "source_name": source_name}

        poster_link = get_poster_link(imdb_id)
        poster_links[task_id] = poster_link
        if poster_link:
            print(f"Task ID: {task_id}, IMDb ID: {imdb_id}, Poster Link: {poster_link}")
        else:
            print(f"Failed to get poster link for IMDb ID: {imdb_id}")

        thread = threading.Thread(target=run_script, args=(imdb_id, source_name, nix, task_id))
        thread.start()

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/')
def queue_status():
    queued_tasks = list(task_queue.queue)
    return render_template('queue.html', running_tasks=running_tasks, queued_tasks=queued_tasks, task_results=task_results, poster_links=poster_links, time=time, enumerate=enumerate)

@app.route('/start-download', methods=['POST'])
def start_download():
    data = request.json
    imdb_id = data.get('imdb_id')
    source_name = data.get('source_name', 'Vidplay')
    auto_dl = True
    nix = data.get('nix', False)
    silent = data.get('silent', False)

    task_id = str(len(progress) + 1)
    progress[task_id] = "Queued"

    poster_link = get_poster_link(imdb_id)
    poster_links[task_id] = poster_link
    if poster_link:
        print(f"[START DOWNLOAD] Task ID: {task_id}, IMDb ID: {imdb_id}, Poster Link: {poster_link}")
    else:
        print(f"[START DOWNLOAD] Failed to get poster link for IMDb ID: {imdb_id}")

    task_queue.put((task_id, imdb_id, source_name, nix))

    process_next_task()

    return jsonify({"task_id": task_id, "position_in_queue": task_queue.qsize()})

@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    if task_id in running_tasks:
        elapsed_time = time.time() - running_tasks[task_id]["start_time"]
        progress_info = {"status": progress[task_id], "elapsed_time": elapsed_time}
    else:
        progress_info = {"status": progress.get(task_id, "Task not found"), "elapsed_time": None}
    return jsonify(progress_info)

@app.route('/remove-task', methods=['POST'])
def remove_task():
    data = request.json
    task_id = data.get('task_id')
    queued_tasks = list(task_queue.queue)
    
    task_queue.queue.clear()
    task_found = False

    for task in queued_tasks:
        if task[0] == task_id:
            task_found = True
        else:
            task_queue.put(task)

    message = "Task removed" if task_found else "Task not found"
    return jsonify({"message": message, "task_id": task_id})

@app.route('/queue-status')
def queue_status_api():
    running = [
        {
            "id": task_id,
            "poster": poster_links.get(task_id),
            "imdb_id": task_info['imdb_id'],
            "source": task_info['source_name'],
            "progress": progress.get(task_id, "Initializing"),
            "elapsed_time": time.time() - task_info['start_time']
        }
        for task_id, task_info in running_tasks.items()
    ]
    
    queued = [
        {
            "id": task[0],
            "poster": poster_links.get(task[0]),
            "imdb_id": task[1],
            "source": task[2]
        }
        for task in list(task_queue.queue)
    ]
    
    completed = [
        {
            "id": task_id,
            "poster": poster_links.get(task_id),
            "imdb_id": result[1],
            "source": result[2],
            "status": result[0]
        }
        for task_id, result in task_results.items()
    ]
    
    return jsonify({
        "running_tasks": running,
        "queued_tasks": queued,
        "completed_tasks": completed
    })

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import subprocess
import threading
import time
from queue import Queue

app = Flask(__name__)

# Configuration
MAX_SIMULTANEOUS_TASKS = 2  # Configurable number of simultaneous tasks

# Task Management
task_queue = Queue()
running_tasks = {}
task_results = {}
progress = {}

def run_script(imdb_id, source_name, auto_dl, silent, task_id):
    start_time = time.time()
    command = f'python getimdb.py --media-id {imdb_id} --source {source_name}'
    if auto_dl:
        command += ' --auto-download'
    if silent:
        command += ' --silent'

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for line in iter(process.stdout.readline, b''):
        progress[task_id] = line.decode().strip()

    process.stdout.close()
    process.wait()
    elapsed_time = time.time() - start_time
    progress[task_id] = f"Completed in {elapsed_time:.2f} seconds"
    task_results[task_id] = progress[task_id]
    running_tasks.pop(task_id, None)
    process_next_task()

def process_next_task():
    while len(running_tasks) < MAX_SIMULTANEOUS_TASKS and not task_queue.empty():
        task_id, imdb_id, source_name, auto_dl, silent = task_queue.get()
        running_tasks[task_id] = {"start_time": time.time(), "imdb_id": imdb_id, "source_name": source_name}
        thread = threading.Thread(target=run_script, args=(imdb_id, source_name, auto_dl, silent, task_id))
        thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/queue')
def queue_status():
    queued_tasks = list(task_queue.queue)
    return render_template('queue.html', running_tasks=running_tasks, queued_tasks=queued_tasks, task_results=task_results, time=time, enumerate=enumerate)


@app.route('/start-download', methods=['POST'])
def start_download():
    data = request.json
    imdb_id = data.get('imdb_id')
    source_name = data.get('source_name', 'Vidplay')
    auto_dl = data.get('auto_dl', False)
    silent = data.get('silent', False)

    task_id = str(len(progress) + 1)
    progress[task_id] = "Queued"
    task_queue.put((task_id, imdb_id, source_name, auto_dl, silent))

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

if __name__ == '__main__':
    app.run(debug=True)

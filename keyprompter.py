import subprocess, time
from flask import Flask, render_template
from flask_socketio import SocketIO

get_presenter_notes_applescript = '''
tell application "Keynote"
    set theDocument to front document
    set theSlide to current slide of theDocument
    set notesContent to presenter notes of theSlide
end tell
return notesContent
'''

app = Flask(__name__)
socketio = SocketIO(app)

def run_applescript(script):
    process = subprocess.Popen(
        ["osascript", "-e", script], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return stdout.decode("utf-8").strip()
    else:
        return f"AppleScript failed with error: {stderr.decode('utf-8').strip()}"

def watch_presenter_notes(callback, sleep_time=0.1):
    prev_notes = ""
    while (True):
        notes = run_applescript(get_presenter_notes_applescript)
        if notes != prev_notes:
            prev_notes = notes
            callback(notes)
        time.sleep(sleep_time)
    
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    initial_notes = run_applescript(get_presenter_notes_applescript)
    socketio.emit('new_notes', {'notes': initial_notes})

def send_notes_to_web(notes):
    socketio.emit('new_notes', {'notes': notes})

if __name__ == "__main__":
    socketio.start_background_task(target=watch_presenter_notes, callback=send_notes_to_web)
    socketio.run(app, host='0.0.0.0', port=80, debug=True)
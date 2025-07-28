import os
import subprocess
import uuid
import pathlib
from flask import Flask, request, send_from_directory
import PySimpleGUI as sg
import google.generativeai as genai

OUTPUT_DIR = os.path.join(os.getcwd(), "compressed")

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def convert_obj_to_glb(input_path, tmp_glb):
    cmd = ["assimp", "export", input_path, tmp_glb]
    subprocess.check_call(cmd)


def compress_glb_with_draco(input_glb, output_glb):
    cmd = ["gltf-pipeline", "-i", input_glb, "-o", output_glb, "-d", "-c", "10"]
    subprocess.check_call(cmd)


def compress_file(input_path):
    ensure_output_dir()
    tmp = None
    ext = pathlib.Path(input_path).suffix.lower()
    if ext == ".obj":
        tmp = os.path.join(OUTPUT_DIR, f"tmp_{uuid.uuid4().hex}.glb")
        convert_obj_to_glb(input_path, tmp)
        src = tmp
    else:
        src = input_path
    output_path = os.path.join(OUTPUT_DIR, f"{uuid.uuid4().hex}.glb")
    compress_glb_with_draco(src, output_path)
    if tmp and os.path.exists(tmp):
        os.remove(tmp)
    return output_path


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        if 'model' not in request.files:
            return 'No file', 400
        f = request.files['model']
        if not f.filename:
            return 'No filename', 400
        filepath = os.path.join(OUTPUT_DIR, f.filename)
        f.save(filepath)
        out = compress_file(filepath)
        return f'<a href="/download/{os.path.basename(out)}">Download compressed file</a>'
    return '''<form method="post" enctype="multipart/form-data">\n              <input type="file" name="model" />\n              <input type="submit" />\n              </form>'''


@app.route('/download/<name>')
def download_file(name):
    return send_from_directory(OUTPUT_DIR, name, as_attachment=True)


def start_server(port):
    import threading, webbrowser
    def run():
        app.run(port=port)
    threading.Thread(target=run, daemon=True).start()
    webbrowser.open(f'http://localhost:{port}')


def gui():
    sg.theme('DarkBlue3')
    layout = [
        [sg.Text('Select GLB or OBJ file')],
        [sg.Input(key='-FILE-'), sg.FileBrowse()],
        [sg.Text('Gemini API Key'), sg.Input(key='-API-', default_text='')],
        [sg.Button('Compress'), sg.Button('Open Web UI')],
        [sg.Multiline(size=(60,10), key='-LOG-')],
        [sg.Input(key='-QUERY-'), sg.Button('Ask Gemini')],
    ]
    window = sg.Window('Draco Compressor', layout)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Compress':
            path = values['-FILE-']
            if not path:
                window['-LOG-'].print('Please select a file')
                continue
            try:
                out = compress_file(path)
                size = os.path.getsize(out)/1024/1024
                window['-LOG-'].print(f'Saved compressed file to {out} ({size:.2f} MB)')
            except Exception as e:
                window['-LOG-'].print(f'Error: {e}')
        elif event == 'Open Web UI':
            port = 5000
            start_server(port)
        elif event == 'Ask Gemini':
            key = values['-API-']
            query = values['-QUERY-']
            if not key or not query:
                window['-LOG-'].print('Provide API key and query')
                continue
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-pro')
                resp = model.generate_content(query)
                window['-LOG-'].print(resp.text)
            except Exception as e:
                window['-LOG-'].print(f'Gemini error: {e}')
    window.close()


if __name__ == '__main__':
    gui()

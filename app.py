import os
import subprocess
import shutil
import time
import zipfile
from flask import Flask, request, redirect, url_for, send_from_directory
from pydub import AudioSegment

app = Flask(__name__)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Ermine Song Loops</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #000;
            color: #fff;
            font-size: 28px;
            line-height: 1.5;
            font-weight: bold;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 30px;
            background-color: #111;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .logo {
            text-align: center;
            margin-bottom: 10px;
            margin-top: 0;
        }

        .logo img {
            width: 200px;
        }

        h1 {
            text-align: center;
            font-size: 36px;
            margin-bottom: 20px;
            margin-top: 10px;
        }

        .form-group {
            margin-bottom: 20px;
            text-align: center;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            font-size: 24px;
        }

        .form-group input[type="file"], .form-group input[type="text"], .form-group input[type="checkbox"] {
            display: block;
            width: 100%;
            padding: 10px;
            font-size: 20px;
            background-color: #222;
            color: #fff;
            border: none;
            border-radius: 5px;
        }

        .form-group input[type="submit"] {
            background-color: #ff0;
            color: #000;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 24px;
            cursor: pointer;
            margin: 0 auto;
        }

        .form-group input[type="submit"]:hover {
            background-color: #ee0;
        }

        .about-section {
            margin-top: 10px;
            margin-bottom: 10px;
            text-align: center;
            font-size: 18px;
            color: #ccc;
        }

        .usage-title {
            font-weight: bold;
        }

        .usage-text {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="/static/logo.png" alt="Ermine Song Loops Logo">
        </div>
        <h1>Ermine Song Loops</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="music">Choose .mp3, .wav files:</label>
                <input type="file" name="music" id="music" accept=".mp3, .wav" multiple>
            </div>
            <div class="form-group">
                <label for="triplicate">Loop 3 times</label>
                <input type="checkbox" name="triplicate" id="triplicate" style="transform: scale(1.5);">
            </div>
            <div class="form-group">
                <input type="submit" value="Upload">
            </div>
        </form>
        <form action="/process" method="post">
            <div class="form-group">
                <label for="url">Or enter a YouTube URL:</label>
                <input type="text" name="url" id="url">
            </div>
            <div class="form-group">
                <label for="triplicate">Loop 3 times</label>
                <input type="checkbox" name="triplicate" id="triplicate" style="transform: scale(1.5);">
            </div>
            <div class="form-group">
                <input type="submit" value="Process">
            </div>
        </form>
        <div class="about-section">
            A simple site for generating perfect song loops. Max. size: 100 MB. An Ermine project.
            <div class="usage-text">Creates prefectly loopable song cuts for easy repetition.</div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/upload', methods=['POST'])
def upload():
    # Check if the 'music' files are present in the request
    if 'music' not in request.files:
        return redirect(url_for('error'))

    files = request.files.getlist('music')
    triplicate = 'triplicate' in request.form

    looped_files = []
    output_folder = os.path.join(app.root_path, 'temp', 'LooperOutput')

    os.makedirs(output_folder, exist_ok=True)  # Create the 'LooperOutput' directory if it doesn't exist

    for file in files:
        # Save each uploaded file to a temporary location
        filename = file.filename
        file_path = os.path.join(app.root_path, 'temp', filename)
        file.save(file_path)

        looped_filepath = process_file(file_path, output_folder, triplicate)
        if looped_filepath:
            looped_files.append(looped_filepath)

    # Provide the download links to the user
    if len(looped_files) == 1:
        return send_from_directory(output_folder, looped_files[0], as_attachment=True)
    else:
        # Create a zip file containing the looped files
        zip_filename = 'looped_files.zip'
        zip_filepath = os.path.join(app.root_path, 'temp', zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            for looped_file in looped_files:
                looped_filepath = os.path.join(output_folder, looped_file)
                zip_file.write(looped_filepath, looped_file)

        return send_from_directory(os.path.join(app.root_path, 'temp'), zip_filename, as_attachment=True)

@app.route('/process', methods=['POST'])
def process():
    url = request.form.get('url')

    if url:
        # Check if the URL is from YouTube
        if 'youtube.com' not in url:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Invalid URL</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #000;
                        color: #fff;
                        font-size: 28px;
                        line-height: 1.5;
                        font-weight: bold;
                        text-align: center;
                    }
                    .message {
                        margin-top: 100px;
                    }
                </style>
            </head>
            <body>
                <div class="message">
                    <h1>Invalid URL</h1>
                    <p>Sadly, only YouTube URLs are supported.</p>
                </div>
            </body>
            </html>
            '''

        triplicate = 'triplicate' in request.form
        output_folder = os.path.join(app.root_path, 'temp', 'LooperOutput')

        os.makedirs(output_folder, exist_ok=True)  # Create the 'LooperOutput' directory if it doesn't exist

        looped_filename = process_url(url, output_folder, triplicate)
        if looped_filename:
            return send_from_directory(output_folder, looped_filename, as_attachment=True)

    return redirect(url_for('error'))

def process_file(file_path, output_folder, triplicate):
    # Run the music looping script using subprocess
    script_path = 'pymusiclooper'  # Assuming the script is in the current directory or on the PATH
    output_filename = f'{os.path.splitext(os.path.basename(file_path))[0]}-loop{os.path.splitext(file_path)[1]}'
    output_filepath = os.path.join(output_folder, output_filename)

    command = [script_path, 'split-audio', '--path', file_path]

    subprocess.run(command, cwd=app.root_path)

    # Wait for the output file to be generated
    time.sleep(2)

    # Move the generated file to the 'LooperOutput' folder
    generated_filename = os.path.basename(file_path) + '-loop.wav'
    generated_filepath = os.path.join(output_folder, generated_filename)

    if os.path.exists(generated_filepath):
        shutil.move(generated_filepath, output_filepath)
        
        if triplicate:
            triplicated_filename = triplicate_audio(output_filepath)
            if triplicated_filename:
                return triplicated_filename
        
        return output_filename

    return None

def process_url(url, output_folder, triplicate):
    # Run the music looping script using subprocess with the URL
    script_path = 'pymusiclooper'  # Assuming the script is in the current directory or on the PATH

    command = [script_path, 'split-audio', '--url', url]

    try:
        subprocess.run(command, cwd=app.root_path, check=True)

    except subprocess.CalledProcessError as e:
        # An error occurred during the execution of the music looping script
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error Processing URL</title>
            <style>
                ...
            </style>
        </head>
        <body>
            <div class="message">
                <h1>Error Processing URL</h1>
                <p>An error occurred while processing the URL.</p>
                <p>Error Output:</p>
                <pre>{}</pre>
                <p>Error: {}</p>
            </div>
        </body>
        </html>
        '''.format(e.output, e)

    except Exception as e:
        # An exception occurred while running the subprocess command
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error Processing URL</title>
            <style>
                ...
            </style>
        </head>
        <body>
            <div class="message">
                <h1>Error Processing URL</h1>
                <p>An error occurred while processing the URL.</p>
                <p>Error: {}</p>
            </div>
        </body>
        </html>
        '''.format(str(e))

    # Wait for the output files to be generated
    time.sleep(2)

    # Check if any files were generated in the output folder
    files_in_output_folder = os.listdir(output_folder)
    if not files_in_output_folder:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>No Files Generated</title>
            <style>
                ...
            </style>
        </head>
        <body>
            <div class="message">
                <h1>No Files Generated</h1>
                <p>No looped files were generated for the given URL.</p>
            </div>
        </body>
        </html>
        '''

    # Find the looped file
    loop_filename = None
    for filename in files_in_output_folder:
        if filename.endswith('.opus-loop.wav'):
            loop_filename = filename
            break

    if loop_filename is None:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>No Loop File Found</title>
            <style>
                ...
            </style>
        </head>
        <body>
            <div class="message">
                <h1>No Loop File Found</h1>
                <p>No looped file was generated for the given URL.</p>
            </div>
        </body>
        </html>
        '''

    # Move the generated loop file to the output folder
    looped_filepath = os.path.join(output_folder, loop_filename)
    loop_filepath = os.path.join(app.root_path, 'temp', 'LooperOutput', loop_filename)

    try:
        os.makedirs(os.path.dirname(loop_filepath), exist_ok=True)
        shutil.move(looped_filepath, loop_filepath)
    except Exception as e:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error Moving File</title>
            <style>
                ...
            </style>
        </head>
        <body>
            <div class="message">
                <h1>Error Moving File</h1>
                <p>An error occurred while moving the generated file. Error: {error}</p>
            </div>
        </body>
        </html>
        '''.format(error=str(e))

    if triplicate:
        triplicated_filename = triplicate_audio(loop_filepath)
        if triplicated_filename:
            return triplicated_filename

    # Provide the download link to the user for the looped file
    return loop_filename

def triplicate_audio(audio_path):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path, format='wav')

    # Triplicate the audio by appending copies
    triplicated_audio = audio + audio + audio

    # Export the triplicated audio to a new file
    triplicated_filename = os.path.splitext(os.path.basename(audio_path))[0] + '-triplicate.wav'
    triplicated_filepath = os.path.join(app.root_path, 'temp', 'LooperOutput', triplicated_filename)

    triplicated_audio.export(triplicated_filepath, format='wav')

    return triplicated_filename

@app.route('/download')
def download():
    filenames = request.args.get('filenames')

    if filenames:
        filenames = filenames.split(',')

        # Create a zip file containing the looped files
        zip_filename = 'looped_files.zip'
        zip_filepath = os.path.join(app.root_path, 'temp', zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            for filename in filenames:
                looped_filepath = os.path.join(app.root_path, 'temp', 'LooperOutput', filename)
                zip_file.write(looped_filepath, os.path.basename(looped_filepath))

        return send_from_directory(os.path.join(app.root_path, 'temp'), zip_filename, as_attachment=True)

    return redirect(url_for('error'))


@app.route('/error')
def error():
    # Handle error cases
    return 'Error: File upload failed.'

@app.route('/static/logo.png')
def get_logo():
    # Serve the logo file
    return send_from_directory('static', 'logo.png')

if __name__ == '__main__':
    app.run()

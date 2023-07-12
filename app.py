import os
import subprocess
import shutil
import time
from flask import Flask, request, redirect, url_for, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Ermine song loops</title>
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
            padding: 60px;
            background-color: #111;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .logo {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo img {
            width: 250px;
        }

        h1 {
            text-align: center;
            font-size: 48px;
            margin-bottom: 40px;
        }

        .form-group {
            margin-bottom: 40px;
            text-align: center;
        }

        .form-group label {
            display: block;
            margin-bottom: 20px;
            font-size: 32px;
        }

        .form-group input[type="file"], .form-group input[type="text"] {
            display: block;
            width: 100%;
            padding: 20px;
            font-size: 32px;
            background-color: #222;
            color: #fff;
            border: none;
            border-radius: 5px;
        }

        .form-group input[type="submit"] {
            background-color: #ff0;
            color: #000;
            padding: 20px 40px;
            border: none;
            border-radius: 5px;
            font-size: 32px;
            cursor: pointer;
            margin: 0 auto;
        }

        .form-group input[type="submit"]:hover {
            background-color: #ee0;
        }

        .about-section {
            margin-top: 60px;
            text-align: center;
            font-size: 24px;
            color: #ccc;
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
                <input type="submit" value="Upload">
            </div>
        </form>
        <form action="/process" method="post">
            <div class="form-group">
                <label for="url">Enter YouTube URL:</label>
                <input type="text" name="url" id="url">
            </div>
            <div class="form-group">
                <input type="submit" value="Process">
            </div>
        </form>
        <div class="about-section">
            A simple site for generating perfect song loops. Supports batch file upload. An <a href="https://ermine.de">Ermine</a> project.
        </div>
    </div>
</body>
</html>
'''

# Serve the favicon file
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/upload', methods=['POST'])
def upload():
    # Check if the 'music' files are present in the request
    if 'music' not in request.files:
        return redirect(url_for('error'))

    files = request.files.getlist('music')

    looped_files = []

    os.makedirs('temp', exist_ok=True)  # Create the 'temp/' directory if it doesn't exist

    for file in files:
        # Save each uploaded file to a temporary location
        filename = file.filename
        file_path = os.path.join('temp', filename)
        file.save(file_path)


        # Run the music looping script using subprocess
        script_path = 'pymusiclooper'  # Assuming the script is in the current directory or on the PATH
        output_folder = os.path.join('temp', 'LooperOutput')
        output_filename = f'{os.path.splitext(filename)[0]}-loop{os.path.splitext(filename)[1]}'
        output_filepath = os.path.join(output_folder, output_filename)

        command = [script_path, 'split-audio', '--path', file_path]

        subprocess.run(command)

        # Wait for the output file to be generated
        time.sleep(2)

        # Move the generated file to the 'LooperOutput' folder
        generated_filename = filename + '-loop.wav'
        generated_filepath = os.path.join('temp', 'LooperOutput', generated_filename)

        os.makedirs(output_folder, exist_ok=True)
        shutil.move(generated_filepath, output_filepath)

        looped_files.append(output_filename)

    # Provide the download links to the user
    return redirect(url_for('download', filenames=','.join(looped_files)))

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

        # Run the music looping script using subprocess with the URL
        script_path = 'pymusiclooper'  # Assuming the script is in the current directory or on the PATH
        output_folder = os.path.join('temp', 'LooperOutput')

        command = [script_path, 'split-audio', '--url', url]

        try:
            # Capture the output and error streams
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                # An error occurred during the execution of the music looping script
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error Processing URL</title>
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
                        <h1>Error Processing URL</h1>
                        <p>An error occurred while processing the URL.</p>
                        <p>Error Output:</p>
                        <pre>{}</pre>
                        <p>Error: {}</p>
                    </div>
                </body>
                </html>
                '''.format(result.stdout, result.stderr)

        except Exception as e:
            # An exception occurred while running the subprocess command
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error Processing URL</title>
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
                    <h1>No Files Generated</h1>
                    <p>No looped files were generated for the given URL.</p>
                </div>
            </body>
            </html>
            '''

        # Generate the output filenames using the scheme "outputloop-suffix.wav"
        loop_filename = 'outputloop.wav'
        loop_filepath = os.path.join(output_folder, loop_filename)

        # Move the generated loop file to the output folder, overwriting if it already exists
        looped_filename = files_in_output_folder[0]
        looped_filepath = os.path.join(output_folder, looped_filename)

        try:
            shutil.move(looped_filepath, loop_filepath, copy_function=shutil.copy2)
        except Exception as e:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error Moving File</title>
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
                    <h1>Error Moving File</h1>
                    <p>An error occurred while moving the generated file. Error: {error}</p>
                </div>
            </body>
            </html>
            '''.format(error=str(e))

        # Provide the download link to the user for the looped file only
        return redirect(url_for('download', filenames=loop_filename))

    return redirect(url_for('error'))

import zipfile

@app.route('/download')
def download():
    filenames = request.args.get('filenames')

    if filenames:
        filenames = filenames.split(',')

        # Create a zip file containing the looped files
        zip_filename = 'looped_files.zip'
        zip_filepath = os.path.join('temp', zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            for filename in filenames:
                looped_filepath = os.path.join('temp', 'LooperOutput', filename)
                zip_file.write(looped_filepath, os.path.basename(looped_filepath))

        return send_from_directory('temp', zip_filename, as_attachment=True)

    return redirect(url_for('error'))

@app.route('/error')
def error():
    # Handle error cases
    return 'Error: File upload failed.'

@app.route('/static/logo.png')
def get_logo():
    # Serve the logo file
    return send_from_directory('static', 'logo.png')

@app.route('/ermine')
def ermine_redirect():
    # Redirect to the Ermine website
    return redirect('https://ermine.de')

if __name__ == '__main__':
    app.run()
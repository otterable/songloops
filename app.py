from flask import Flask, render_template, request, send_from_directory, redirect, url_for, Response, send_file
import os
import subprocess
import shutil
import time
import zipfile
from pydub import AudioSegment
import re

app = Flask(__name__, static_url_path='/static')

def get_soundscapes():
    soundscapes = []
    soundscapes_path = os.path.join(app.static_folder, 'soundscapes')
    for folder in os.listdir(soundscapes_path):
        if os.path.isdir(os.path.join(soundscapes_path, folder)):
            soundscapes.append(folder)
    return soundscapes

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    soundscapes = get_soundscapes()
    return render_template('index.html', soundscapes=soundscapes)

@app.route('/upload', methods=['POST'])
def upload():
    if 'music' not in request.files:
        return redirect(url_for('error'))

    files = request.files.getlist('music')
    triplicate = 'triplicate' in request.form

    looped_files = []
    output_folder = os.path.join(app.root_path, 'temp', 'LooperOutput')
    os.makedirs(output_folder, exist_ok=True)

    for file in files:
        filename = file.filename
        file_path = os.path.join(app.root_path, 'temp', filename)
        file.save(file_path)

        looped_filepath = process_file(file_path, output_folder, triplicate)
        if looped_filepath:
            looped_files.append(looped_filepath)

    if len(looped_files) == 1:
        file_path = os.path.join(output_folder, looped_files[0])
        return send_file(file_path, as_attachment=True, download_name=looped_files[0], mimetype='audio/mpeg')
    else:
        zip_filename = 'looped_files.zip'
        zip_filepath = os.path.join(app.root_path, 'temp', zip_filename)
        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            for looped_file in looped_files:
                looped_filepath = os.path.join(output_folder, looped_file)
                zip_file.write(looped_filepath, looped_file)
        return send_file(zip_filepath, as_attachment=True, download_name=zip_filename, mimetype='application/zip')

@app.route('/process', methods=['POST'])
def process():
    url = request.form.get('url')

    if url:
        # Check if the URL is from YouTube
        if 'youtube.com' not in url:
            return render_template('invalid_url.html')

        triplicate = 'triplicate' in request.form

        # Corrected the output_folder for YouTube-generated files
        user_uploaded_output_folder = os.path.join(app.root_path, 'temp', 'LooperOutput')
        youtube_output_folder = os.path.join(app.root_path, 'LooperOutput')

        os.makedirs(youtube_output_folder, exist_ok=True)  # Create the 'LooperOutput' directory if it doesn't exist

        # Process the URL and get the looped filename
        looped_filename = process_url(url, youtube_output_folder, triplicate)

        # Check if the response is a string (HTML error message) instead of a filename
        if not isinstance(looped_filename, str):
            return looped_filename  # Return the error message directly instead of trying to send it as a file

        # Continue with the normal flow for sending the looped file
        return send_loop_file(youtube_output_folder, looped_filename, triplicate)

    return redirect(url_for('error'))

def send_loop_file(output_folder, looped_filename, triplicate):
    # Check if the looped file exists
    looped_filepath = os.path.join(output_folder, looped_filename)
    if not os.path.exists(looped_filepath):
        return render_template('no_loop_file.html')

    if triplicate:
        triplicated_filename = triplicate_audio(looped_filepath)
        if triplicated_filename:
            # Remove square brackets from the triplicated filename
            triplicated_filename_cleaned = re.sub(r'\[|\]', '', triplicated_filename)
            looped_filename = triplicated_filename_cleaned

    # If triplicate is not enabled, directly send the looped file for download
    return download_loop_file(looped_filepath, looped_filename)

def download_loop_file(filepath, filename):
    # Function to send the looped file for download
    def generate():
        with open(filepath, 'rb') as file:
            yield from file

    # Create a custom response to send the looped file as an attachment
    response = send_file(os.path.join(output_folder, looped_files[0]), mimetype='audio/mpeg', as_attachment=True)
    response.headers['Content-Type'] = 'audio/mpeg'
    return response
    
    return redirect(url_for('error'))

def send_loop_file(output_folder, looped_filename, triplicate):
    # Check if the looped file exists
    looped_filepath = os.path.join(output_folder, looped_filename)
    if not os.path.exists(looped_filepath):
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

    if triplicate:
        triplicated_filename = triplicate_audio(looped_filepath)
        if triplicated_filename:
            # Remove square brackets from the triplicated filename
            triplicated_filename_cleaned = re.sub(r'\[|\]', '', triplicated_filename)
            looped_filename = triplicated_filename_cleaned

    # If triplicate is not enabled, directly send the looped file for download
    return send_from_directory(output_folder, looped_filename, as_attachment=True)

    return redirect(url_for('error'))

def process_file(file_path, output_folder, triplicate):
    # Run the music looping script using subprocess
    script_path = 'pymusiclooper'  # Assuming the script is in the current directory or on the PATH
    output_filename = f'{os.path.splitext(os.path.basename(file_path))[0]}-loop{os.path.splitext(file_path)[1]}'
    output_filepath = os.path.join(output_folder, output_filename)

    command = [script_path, 'split-audio', '--path', file_path, '--min-duration-multiplier', '0.15']

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
    time.sleep(5)  # Increase the waiting time to ensure the file is fully downloaded and ready

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

    # Sort files by modification date (newest to oldest)
    files_in_output_folder.sort(key=lambda x: os.path.getmtime(os.path.join(output_folder, x)), reverse=True)

    # Find the looped file with the latest modification date
    loop_filename = None
    for filename in files_in_output_folder:
        if filename.endswith('.opus-loop.wav'):
            loop_filename = filename
            break

    if loop_filename is None:
        print("Error: No Loop File Found for the given URL. Directory:", output_folder)
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

    # Remove square brackets from the filename
    loop_filename_cleaned = re.sub(r'\[|\]', '', loop_filename)

    # Move the generated loop file to the output folder
    looped_filepath = os.path.join(output_folder, loop_filename)
    loop_filepath = os.path.join(output_folder, loop_filename_cleaned)

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
        # Triplicate the audio file and save the triplicated file
        triplicated_filepath = triplicate_audio(loop_filepath)
        if triplicated_filepath:
            # Remove square brackets from the triplicated filename
            triplicated_filename_cleaned = re.sub(r'\[|\]', '', os.path.basename(triplicated_filepath))
            triplicated_output_filepath = os.path.join(output_folder, triplicated_filename_cleaned)
            try:
                shutil.move(triplicated_filepath, triplicated_output_filepath)
            except Exception as e:
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error Moving Triplicated File</title>
                    <style>
                        ...
                    </style>
                </head>
                <body>
                    <div class="message">
                        <h1>Error Moving Triplicated File</h1>
                        <p>An error occurred while moving the triplicated file. Error: {error}</p>
                    </div>
                </body>
                </html>
                '''.format(error=str(e))
            return triplicated_filename_cleaned  # Return the triplicated file name


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
                looped_filepath = os.path.join(app.root_path, 'LooperOutput', filename)  # Fixed the file path here
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

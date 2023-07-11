import os
import shutil
from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['music']
    filename = file.filename
    filepath = os.path.join('temp', filename)
    file.save(filepath)

    output_filename = os.path.splitext(filename)[0] + '-loop.mp3'
    output_filepath = os.path.join('temp', 'LooperOutput', output_filename)

    # Run the pymusiclooper script
    command = ['pymusiclooper', 'split-audio', '--path', filepath]
    subprocess.run(command)

    # Move the generated file to the output directory
    shutil.move(filepath + '-loop.wav', output_filepath)

    return f'File uploaded and processed successfully! Output file: {output_filename}'

if __name__ == '__main__':
    app.run(debug=True)
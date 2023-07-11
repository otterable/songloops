from flask import Flask, send_from_directory
app = Flask(__name__)

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('C:/Users/ottr/Desktop/Webseiten/otterable6.github.io/static', filename)

@app.route('/')
def serve_index():
    return send_from_directory('C:/Users/ottr/Desktop/Webseiten/otterable6.github.io/static', 'index.html')

app.debug = True

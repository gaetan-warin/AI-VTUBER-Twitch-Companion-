import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory, make_response
from flask_socketio import SocketIO
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configure CORS properly for production
socketio = SocketIO(app, cors_allowed_origins="*")

# Unified model serving route using blueprint-like structure
MODEL_BASE = 'model/shizuku'

@app.route('/')
def home():
    return render_template('avatar.html')

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

#action
@socketio.on('speak')
def handle_speak(data):
    """Handle speech request and broadcast to all clients"""
    text = data.get('text', '').strip()
    if text:
        # Broadcast to all connected clients
        socketio.emit('speak_text', {'text': text})

# Model serving routes
@app.route('/model/shizuku/<path:filename>')
def serve_shizuku(filename):
    return send_from_directory('model/shizuku', filename)  # Directory path

@app.route('/model/shizuku/shizuku1024/<path:filename>')
def serve_textures(filename):
    return send_from_directory('model/shizuku/shizuku1024', filename)

@app.route('/model/shizuku/expressions/<path:filename>')
def serve_expressions(filename):
    return send_from_directory('model/shizuku/expressions', filename)

@app.route('/model/shizuku/motions/<path:filename>')
def serve_motions(filename):
    return send_from_directory('model/shizuku/motions', filename)

@app.route('/model/shizuku/sounds/<path:filename>')
def serve_sounds(filename):
    return send_from_directory('model/shizuku/sounds', filename)

#SOCKET IO BAS
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=os.environ.get('DEBUG', False))

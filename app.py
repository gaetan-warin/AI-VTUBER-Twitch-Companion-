import os
import eventlet
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv
import ollama
import re
import json

# Monkey patching for eventlet compatibility
eventlet.monkey_patch(thread=True, os=True, select=True, socket=True)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Ollam CFG
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
PRE_PROMPT = os.getenv("PRE_PROMPT")
PERSONA_NAME = os.getenv("PERSONA_NAME")
PERSONA_ROLE = os.getenv("PERSONA_ROLE")

# Socket.IO CFG
SOCKETIO_IP = os.getenv("SOCKETIO_IP")
SOCKETIO_IP_PORT = os.getenv("SOCKETIO_IP_PORT")

# CURRENT SERVER CFG
API_URL = os.getenv("API_URL")
API_URL_PORT = os.getenv("API_URL_PORT")

DEFAULT_AVATAR_MODEL = os.getenv("API_URL_PORT")

# Configure SocketIO with CORS and async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# Serve the home page
@app.route('/')
def home():
    return render_template('avatar.html')

# Trigger speak endpoint
@app.route('/trigger_speak', methods=['POST'])
def trigger_speak():
    data = request.get_json()
    text = data.get('text', '').strip()

    if text:
        socketio.emit('speak_text', {'text': text})
        return jsonify({'status': 'success', 'message': 'Text sent to speak'}, 200)
    return jsonify({'status': 'error', 'message': 'No text provided'}, 400)

@app.route('/trigger_ai_request', methods=['POST'])
def trigger_ai_request():
    print("in trigger_ai_request")
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
        user_input = data.get('message', '').strip()
        response, status_code = process_ai_request(user_input)
        if status_code == 200:
            socketio.emit('speak_text', {'text': response['message']})
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_model', methods=['GET'])
def getModel():
    avatar_model_path = "models/shizuku/shizuku.model.json"
    if (avatar_model_path ==  "shizuku"):
        avatar_model_path = "models/shizuku/shizuku.model.json"
    return avatar_model_path


def process_ai_request(user_input):
    if not user_input:
        return {'status': 'error', 'message': 'No message provided'}, 400

    if not OLLAMA_MODEL:
        return {'status': 'error', 'message': 'Missing OLLAMA configuration'}, 500

    # Create a structured prompt
    structured_prompt = f"""
    Persona:
    Name: {PERSONA_NAME}
    Role: {PERSONA_ROLE}

    Instructions:
    {PRE_PROMPT}

    User: {user_input}
    """

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": structured_prompt.strip()}])
        final_response = response['message']['content'].strip()
        cleaned_response = clean_response(final_response)
        return {'status': 'success', 'message': cleaned_response}, 200
    except Exception as e:
        return {'status': 'error', 'message': f'Request error: {str(e)}'}, 500

def clean_response(response):
    response = re.sub(r'<think>\s*.*?\s*</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'[^\x00-\x7F]+', '', response)
    response = re.sub(r'\\_\\_\\_', '', response)
    response = re.sub(r'\s+', ' ', response).strip()
    return response

# Serve model files and resources (textures, expressions, motions, sounds)
@app.route('/models/<path:filename>')
def serve_model_files(filename):
    models_dir = os.path.join(app.root_path, 'models')
    if os.path.isfile(os.path.join(models_dir, filename)):
        return send_from_directory(models_dir, filename)
    else:
        abort(404)

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('speak')
def handle_speak(data):
    text = data.get('text', '').strip()
    if text:
        socketio.emit('speak_text', {'text': text})

@socketio.on('request_model_path')
def handle_request_model_path():
    avatar_model_path = "models/shizuku/shizuku.model.json"
    socketio.emit('model_path', {'path': avatar_model_path})

@socketio.on('ask_ai')
def handle_ask_ai(data):
    user_input = data.get('text', '').strip()
    response, status_code = process_ai_request(user_input)
    if status_code == 200:
        socketio.emit('ai_response', {'text': response['message']})

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

# Main entry point
if __name__ == '__main__': 
    try: 
        print(f"\n🔥 Starting server at  {API_URL}:{API_URL_PORT}...") 
        socketio.run(app, host=SOCKETIO_IP, port=SOCKETIO_IP_PORT) 
    except Exception as e: 
        print(f"Error starting server: {e}")

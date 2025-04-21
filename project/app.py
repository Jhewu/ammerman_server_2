from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import socket
import threading
import json
import requests

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# Configuration for TTS Service
TTS_SERVICE_HOST = "127.0.0.1"  # Replace with your Raspberry Pi's IP address
TTS_SERVICE_PORT = 3001

# Function to forward messages to the TTS service
def send_to_tts_service(message):
    try:
        # Connect to the TTS service
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TTS_SERVICE_HOST, TTS_SERVICE_PORT))
            # Send the message
            s.sendall(message.encode('utf-8'))
        return True
    except Exception as e:
        print(f"Error sending to TTS service: {e}")
        return False

# TCP Server Thread - receives text from external clients
def tcp_server():
    host = '0.0.0.0'
    port = 3002  # Different port than TTS service
    
    # Start the TCP/IP Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"TCP Server listening on {host}:{port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        
        with client_socket:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Decode the message
                msg = data.decode('utf-8')
                print("Received text to speak:", msg)
                
                # Forward to TTS service
                send_to_tts_service(msg)

@app.route('/')
def index():
    return render_template('index.html')

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# This endpoint will be called by the TTS service to update captions
@app.route('/tts/update', methods=['POST'])
def tts_update():
    data = request.json
    if 'event' in data:
        if data['event'] == 'new_caption':
            socketio.emit('new_caption', {'text': data['text']})
        elif data['event'] == 'finished':
            socketio.emit('finished')
    return {'status': 'ok'}

if __name__ == '__main__':
    # Start the TCP server thread
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)
    tcp_thread.start()
    
    # Start the Flask app with Socket.IO
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading
import pyttsx3
import queue
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

# Global variables
tts_queue = queue.Queue()
tts_lock = threading.Lock()
speech_active = False

# TTS thread function
def tts_worker():
    global speech_active
    
    # Initialize TTS engine just once
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)  # Even slower rate
    engine.setProperty('volume', 1.0)  # Maximum volume
    
    # Define callbacks
    def onStart(name):
        nonlocal current_text
        socketio.emit('new_caption', {'text': current_text})
        print(f"Started speaking: {current_text}")
    
    def onEnd(name, completed):
        socketio.emit('finished')
        print(f"Finished speaking: {name}, completed: {completed}")
    
    # Connect callbacks
    engine.connect('started-utterance', onStart)
    engine.connect('finished-utterance', onEnd)
    
    while True:
        try:
            # Get the next message from queue
            full_message, client_id = tts_queue.get()
            if full_message is None:  # shutdown signal
                break
            
            # Process message by 4-words chunks
            words = full_message.split()
            word_buffer = []
            
            for text in words:
                word_buffer.append(text)
                
                if len(word_buffer) >= 4:
                    to_speak = ' '.join(word_buffer[:4])
                    current_text = to_speak
                    print(f"Queuing: {to_speak}")
                    
                    with tts_lock:
                        speech_active = True
                        engine.say(to_speak)
                        engine.runAndWait()
                        # Add a small pause between segments
                        # time.sleep(0.2)
                        speech_active = False
                    
                    word_buffer = word_buffer[4:]
            
            # Handle remaining words
            if word_buffer:
                to_speak = ' '.join(word_buffer)
                if len(word_buffer) < 4:
                    to_speak += " dot dot dot"
                
                current_text = to_speak
                print(f"Final segment: {to_speak}")
                
                with tts_lock:
                    speech_active = True
                    engine.say(to_speak)
                    engine.runAndWait()
                    speech_active = False
            
            # Mark task as done
            tts_queue.task_done()
            
        except Exception as e:
            print(f"Error in TTS worker: {e}")
            # Reset speech state in case of error
            speech_active = False

# TCP Server Thread
def tcp_server():
    host = '0.0.0.0'
    port = 3001
    
    # Start the TCP/IP Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"TCP Server listening on {host}:{port}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")
            client_id = f"{addr[0]}:{addr[1]}"
            
            with client_socket:
                while True:
                    # Receive connection from client
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Decode the message
                    msg = data.decode('utf-8')
                    print(f"Received from {client_id}: {msg}")
                    
                    # Only queue if not currently speaking or queue is empty
                    if not speech_active or tts_queue.empty():
                        tts_queue.put((msg, client_id))
                    else:
                        print("Speech already active, skipping message")
                        # Optionally send a response to client
                        client_socket.sendall(b"TTS system busy")
        except Exception as e:
            print(f"TCP server error: {e}")
            # Brief pause to prevent rapid reconnection attempts
            time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    try:
        # Start the TTS worker thread
        tts_thread = threading.Thread(target=tts_worker, daemon=True)
        tts_thread.start()
        
        # Start the TCP server thread
        tcp_thread = threading.Thread(target=tcp_server, daemon=True)
        tcp_thread.start()
        
        # Start the Flask app with Socket.IO
        socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error starting application: {e}")

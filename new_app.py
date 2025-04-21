from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading
import pyttsx3
import queue
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

# Global TTS engine and synchronization queue
tts_queue = queue.Queue()
tts_engine = None

def onEnd(name, completed):
    # Emit that we're done with this segment
    socketio.emit('finished')
    print('finishing', name, completed) 

# TTS thread function
def tts_worker():
    global tts_engine
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 140)

    tts_engine.connect('finished-utterance', onEnd)
    
    while True:
        try:
            text, client_id = tts_queue.get()
            if text is None:  # shutdown signal
                break
                
            # Emit that we're starting to speak this text
            socketio.emit('new_caption', {'text': text})
            
            # Speak the text
            tts_engine.say(text)
            tts_engine.runAndWait()
            
            # Mark task as done
            tts_queue.task_done()
        except Exception as e:
            print(f"Error in TTS worker: {e}")

# TCP Server Thread
def tcp_server():
    host = '0.0.0.0'
    port = 3001
    
    # Start the TCP/IP Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"TCP Server listening on {host}:{port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_id = addr[0] + ":" + str(addr[1])
        
        with client_socket:
            while True:
                # Receive connection from client
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Decode the message
                msg = data.decode('utf-8')
                print("Received:", msg)
                
                # Process message by 4-words chunks
                word_buffer = []
                for text in msg.split():
                    word_buffer.append(text)
                    while len(word_buffer) >= 4:
                        to_speak = ' '.join(word_buffer[:4])
                        print(to_speak, end=' ', flush=True)
                        
                        # Queue the text for speaking
                        tts_queue.put((to_speak, client_id))
                        
                        word_buffer = word_buffer[4:]
                
                # Final flush for remaining words
                if word_buffer:
                    if len(word_buffer) < 4:
                        word_buffer.append("dot dot dot")
                    to_speak = ' '.join(word_buffer)
                    print(to_speak)
                    
                    # Queue the final segment
                    tts_queue.put((to_speak, client_id))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Start the TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    
    # Start the TCP server thread
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)
    tcp_thread.start()
    
    # Start the Flask app with Socket.IO
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True)

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading
import pyttsx3

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

# TCP Server Thread
def tcp_server():
    host = '0.0.0.0'
    port = 3001

    # Initiate text-to-speech model
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)

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

                        # Speak the four works
                        socketio.emit('new_caption', {'text': to_speak})
                        engine.say(to_speak)
                        engine.startLoop()
                        
                        engine.endLoop()
                        word_buffer = word_buffer[4:]
                        socketio.emit('finished')

                # Final flush for remaining words
                if word_buffer:
                    if len(word_buffer) < 4: 
                        word_buffer.append("dot dot dot")
                    else: 
                        to_speak = ' '.join(word_buffer)
                        print(to_speak)

                        socketio.emit('new_caption', {'text': to_speak})
                        engine.say(to_speak)
                        engine.runAndWait()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=tcp_server, daemon=True).start()
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True)

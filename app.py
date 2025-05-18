from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import threading
import pyttsx3
import queue
import argparse
import os

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

# Global TTS engine and synchronization queue
tts_queue = queue.Queue()
tts_engine = None
stop_flag = False

message = ""

def onStart(name): 
    socketio.emit('new_caption', {'text': message})

def onEnd(name, completed):
    # Emit that we're done with this segment
    socketio.emit('finished')
    # print('finishing', name, completed) 

def clear_queue(q):
    with q.mutex:
      q.queue.clear()
      q.all_tasks_done.notify_all()
      q.unfinished_tasks = 0
      q.not_full.notify_all()

# TTS thread function
def tts_worker():
    global tts_engine, message, stop_flag

    tts_engine = pyttsx3.init()

    # Set all properties
    tts_engine.setProperty('rate', 140)
    tts_engine.connect('finished-utterance', onEnd)
    tts_engine.connect('started-utterance', onStart)

    while True:
        try:
            full_message, client_id = tts_queue.get()
            if full_message is None:  # shutdown signal
                break
                
            # Process message by 4-words chunks
            word_buffer = []
            for text in full_message.split():
                word_buffer.append(text)

            while len(word_buffer) >= 4:
                if stop_flag: 
                    tts_engine.stop()
                    clear_queue(tts_queue)
                    break

                to_speak = ' '.join(word_buffer[:4])
                print(to_speak, end=' ', flush=True)
                
                # Emit that we're starting to speak this segment
                # socketio.emit('new_caption', {'text': to_speak})
                
                message = to_speak

                # Speak the text
                tts_engine.say(to_speak)
                tts_engine.runAndWait()
                
                word_buffer = word_buffer[4:]
            
            # Final flush for remaining words
            if word_buffer and not stop_flag:
                if stop_flag: 
                    tts_engine.stop()
                    clear_queue(tts_queue)
                    break

                if len(word_buffer) < 4:
                    word_buffer.append("dot dot dot")
                to_speak = ' '.join(word_buffer)
                tts_engine.say(to_speak)
                tts_engine.runAndWait()
                socketio.emit('new_caption', {'text': to_speak})
                socketio.emit('finished')
                
            # Mark task as done
            if stop_flag:
                stop_flag = False
            else:
                tts_queue.task_done()

            print(f"\nThis is the length of queue after {tts_queue.qsize()}\n")
            
        except Exception as e:
            print(f"Error in TTS worker: {e}")

# TCP Server Thread
def tcp_server(port=3001):
    global stop_flag
    host = '0.0.0.0'

    print(f'\nThis is port {port}')
    
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

                if msg == "STOP_ENGINE": 
                    stop_flag = True
                    print(f"\nSTOPPING ENGINE\n")
                else:                
                    # Simply pass the entire message to the TTS queue
                    tts_queue.put((msg, client_id))

@app.route('/')
def index():
    return render_template('index.html', socket_port=http)

if __name__ == '__main__':
    des="""Initiate the Ammerman (2) servers"""

    # Create command line arguments
    parser = argparse.ArgumentParser(description=des.lstrip(" "),formatter_class=argparse.RawTextHelpFormatter)

    # Add the arguments
    parser.add_argument('--tcp_port',type=int,help='TCP Server Port\t[3001]')
    parser.add_argument('--http_port',type=int,help='HTTP Server Port\t[5001]')
    parser.add_argument('--speaker_id',type=str,help='Find ID using pactl list short sinks\t[2	alsa_output.pci-0000_00_1f.3.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED]')
    parser.add_argument('--voice_index',type=int,help='0 for male and 1 for female\t[0]')
    args = parser.parse_args()

    if args.tcp_port is not None: 
        port = args.tcp_port
    else: raise IOError    
    if args.http_port is not None: 
        http = args.http_port
    else: raise IOError
    if args.speaker_id is not None: 
        speaker_id = args.speaker_id
        os.environ['PULSE_SINK'] = speaker_id
    if args.voice_index is not None: 
        voice_index = args.voice_index
    else: voice_index = 0

    # Start the TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    
    # Start the TCP server thread
    tcp_thread = threading.Thread(target=tcp_server, args=(port, ), daemon=True)
    tcp_thread.start()
    
    # Start the Flask app with Socket.IO
    socketio.run(app, host='localhost', port=http, allow_unsafe_werkzeug=True)

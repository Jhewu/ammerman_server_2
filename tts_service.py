import socket
import threading
import pyttsx3
import queue
import requests
import time

# Configuration for Web Server
WEB_SERVER_HOST = "192.168.1.200"  # Replace with your web server's IP address
WEB_SERVER_PORT = 5000

# Global TTS engine and synchronization queue
tts_queue = queue.Queue()
tts_engine = None

# Function to notify the web server about TTS events
def notify_web_server(event_type, text=""):
    try:
        data = {'event': event_type}
        if text:
            data['text'] = text
            
        url = f"http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}/tts/update"
        requests.post(url, json=data, timeout=3)
    except Exception as e:
        print(f"Error notifying web server: {e}")

def onStart(name):
    # We don't need to do anything here as we're notifying 
    # the web server in the worker thread
    pass

def onEnd(name, completed):
    # We don't need to do anything here as we're notifying 
    # the web server in the worker thread
    pass

# TTS thread function
def tts_worker():
    global tts_engine
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 130)
    tts_engine.connect('finished-utterance', onEnd)
    tts_engine.connect('started-utterance', onStart)

    while True:
        try:
            full_message = tts_queue.get()
            if full_message is None:  # shutdown signal
                break
                
            # Process message by 4-words chunks
            word_buffer = []
            for text in full_message.split():
                word_buffer.append(text)
                while len(word_buffer) >= 4:
                    to_speak = ' '.join(word_buffer[:4])
                    print(to_speak, end=' ', flush=True)
                    
                    # Notify web server about new caption
                    notify_web_server("new_caption", to_speak)
                    
                    # Speak the text
                    tts_engine.say(to_speak)
                    tts_engine.runAndWait()
                    
                    # Notify web server that this segment is done
                    notify_web_server("finished")
                    
                    word_buffer = word_buffer[4:]
            
            # Final flush for remaining words
            if word_buffer:
                if len(word_buffer) < 4:
                    word_buffer.append("dot dot dot")
                to_speak = ' '.join(word_buffer)
                print(to_speak)
                
                # Notify web server about final caption
                notify_web_server("new_caption", to_speak)
                
                # Speak the text
                tts_engine.say(to_speak)
                tts_engine.runAndWait()
                
                # Notify web server that we're done
                notify_web_server("finished")
            
            # Mark task as done
            tts_queue.task_done()
            
        except Exception as e:
            print(f"Error in TTS worker: {e}")

# TCP Server Thread - receives text from web server
def tcp_server():
    host = '0.0.0.0'
    port = 3001
    
    # Start the TCP/IP Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"TTS Service listening on {host}:{port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        
        with client_socket:
            while True:
                # Receive connection from web server
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Decode the message
                msg = data.decode('utf-8')
                print("Received text to speak:", msg)
                
                # Add to TTS queue
                tts_queue.put(msg)

if __name__ == '__main__':
    print("Starting TTS Service...")
    
    # Start the TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    
    # Start the TCP server thread
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)
    tcp_thread.start()
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Shutting down TTS Service...")

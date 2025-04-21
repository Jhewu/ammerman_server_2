import socket

def start_client(host='0.0.0.0', port=3001):
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect the socket to the server's address and port
        client_socket.connect((host, port))
        print(f"Connected to {host}:{port}")

        message = "A chicken nugget is a food product consisting of a small piece of deboned chicken meat that is breaded or battered, then deep-fried or baked. Developed in the 1950s by finding a way to make a coating adhere, chicken nuggets have become a very popular fast food restaurant item, and are widely sold frozen for home use."
        client_socket.sendall(message.encode('utf-8'))

    finally:
        # Clean up the connection
        client_socket.close()

if __name__ == "__main__":
    start_client()
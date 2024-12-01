import socket

def test_client():
    HOST = '127.0.0.1'
    PORT = 8000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(b"Hello, Server!")
        response = client_socket.recv(1024)
        print(f"Response from server: {response.decode('utf-8')}")

if __name__ == "__main__":
    test_client()

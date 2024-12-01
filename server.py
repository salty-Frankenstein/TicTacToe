import socket

class Server:
    def __init__(self, host, port, backlog) -> None:
        self.HOST = host
        self.PORT = port
        self.backlog = backlog  # the backlog of TCP connection

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.HOST, self.PORT))
            server_socket.listen(self.backlog)
            print(f"Server is listening on {self.HOST}:{self.PORT}")

            while True:
                client_socket, client_address = server_socket.accept()
                print(f"Connection established with {client_address}")

                with client_socket:
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break  # client disconnected
                        print(f"Received data: {data.decode('utf-8')}")
                        # reply
                        client_socket.sendall(b"Message received")

if __name__ == "__main__":
    server = Server('127.0.0.1', 8000, 5)
    server.start_server()

import asyncio
import json

class Server:
    def __init__(self, host, port) -> None:
        self.HOST = host
        self.PORT = port

    async def startServer(self):
        server = await asyncio.start_server(self.handleClient, self.HOST, self.PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server is running on {addr}")

        async with server:
            await server.serve_forever()

    async def sendMessage(self, writer, message):
        ''' send message to client
            message is in json format, a dict
        '''
        response_data = json.dumps(message).encode()
        response_length = len(response_data).to_bytes(4, byteorder="big")

        writer.write(response_length + response_data)  
        await writer.drain()

    async def receiveMessage(self, reader):
        ''' receive message from client
            using json as protocol, first 4 bytes for length, following by json data
            return a dict, representing the json data
        '''
        # read 4 bytes for the length of json data
        length_data = await reader.readexactly(4)
        msg_length = int.from_bytes(length_data, byteorder="big")

        # read the json data
        json_data = await reader.readexactly(msg_length)
        message = json.loads(json_data.decode())  
        print(f"Received message: {message}")
        return message

    async def handleClient(self, reader, writer):
        # TODO: finish this
        addr = writer.get_extra_info('peername')
        print(f"New connection from {addr}")

        try:
            while True:
                message = await self.receiveMessage(reader)
                # response
                response = {"status": "ok", "received": message}
                await self.sendMessage(writer, response)
        except asyncio.IncompleteReadError:
            print(f"Connection closed by {addr}")
        finally:
            writer.close()
            await writer.wait_closed()

if __name__ == "__main__":
    server = Server('127.0.0.1', 8000)
    asyncio.run(server.startServer())

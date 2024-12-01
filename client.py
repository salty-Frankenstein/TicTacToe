import asyncio
import json

class Client():
    def __init__(self, host, port) -> None:
        # address of server
        self.HOST = host
        self.PORT = port
    
    async def start(self):
        self.reader, self.writer = await asyncio.open_connection(self.HOST, self.PORT)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def sendMessage(self, message):
        # prepare the json data to send
        json_data = json.dumps(message).encode()
        msg_length = len(json_data).to_bytes(4, byteorder="big")  # length prefix

        # send the prefix + data
        self.writer.write(msg_length + json_data)
        await self.writer.drain()

    async def receiveMessage(self):
        # receive response
        length_data = await self.reader.readexactly(4)  # read the length prefix
        response_length = int.from_bytes(length_data, byteorder="big")
        response_data = await self.reader.readexactly(response_length)
        response = json.loads(response_data.decode())
        return response

async def run():
    client = Client('127.0.0.1',8000)
    await client.start()
    message = {"action": "move", "player": "X", "position": [0, 1]}
    await client.sendMessage(message)
    res = await client.receiveMessage()
    print(f"the result is: {res}")

if __name__ == "__main__":
    asyncio.run(run())

import json

class Message:
    '''
    the base class for sending messages
    '''
    def __init__(self, debug) -> None:
        self.debug = debug

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
        if self.debug:
            print(f"Received message: {message}")
        return message

class Address:
    def __init__(self, host, port) -> None:
        self.HOST, self.PORT = host, port

class MessageServer(Message):
    def __init__(self, debug, address) -> None:
        super().__init__(debug)
        self.address = address

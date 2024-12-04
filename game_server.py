import asyncio
import message as msg
import config

class GameServer(msg.MessageServer):
    '''
    the game server, for the main game logic
    '''

    def __init__(self, address, main_server) -> None:
        super().__init__(True, address)
        self.main_server = main_server

    async def startServer(self):
        server = await asyncio.start_server(
            self.handleMain, self.address.HOST, self.address.PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server is running on {addr}")

        async with server:
            await server.serve_forever()

    async def handleMain(self, reader, writer):
        '''
        main logic, handle the request from main server
        '''


if __name__ == "__main__":
    server = GameServer(config.game_server, config.main_server)
    asyncio.run(server.startServer())
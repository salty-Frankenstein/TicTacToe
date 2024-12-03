import asyncio
import message as msg
import config


class MainServer(msg.MessageServer):
    def __init__(self, address, match_server) -> None:
        super().__init__(True, address)
        self.match_server = match_server

    async def startServer(self):
        server = await asyncio.start_server(
            self.handleClient, self.address.HOST, self.address.PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server is running on {addr}")

        async with server:
            await server.serve_forever()

    async def handleClient(self, reader, writer):
        # TODO: finish this
        addr = writer.get_extra_info('peername')
        print(f"New connection from {addr}")

        try:
            while True:
                message = await self.receiveMessage(reader)
                if message['operation'] == 'match':
                    await self.requestMatch(writer, message['id'])
                elif message['operation'] == 'cancel':
                    await self.requestCancel(writer, message['id'])

                # response
                # response = {"status": "ok", "received": message}
                # await self.sendMessage(writer, response)
        except asyncio.IncompleteReadError:
            print(f"Connection closed by {addr}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def requestMatch(self, client_writer, player_id):
        '''
        request the match server that the player_id client asked to match
        since it won't be a frequent operation
        we start a different connection for each request
        '''
        reader, writer = await asyncio.open_connection(
            self.match_server.HOST, self.match_server.PORT)
        # the request message
        message = {
            'from': 'main',
            'operation': 'match',
            'player_id': player_id
        }
        await self.sendMessage(writer, message)

        # then wait for reply
        response = await self.receiveMessage(reader)

        if response['status'] == 'ok':
            # there's a player ready to match
            # then
            # TODO: tell the game server to start game!
            # TODO: tell the clients to get ready
            # print(f'tell the game server with {response['player_id1']}, {response['player_id2']}')
            pass
        else:
            # there's no player now, tell the client to wait
            message = {
                'status': 'wait',
                'time': 2
            }
            await self.sendMessage(client_writer, message)

    async def requestCancel(self, client_writer, player_id):
        '''
        cancel a match request 
        '''
        reader, writer = await asyncio.open_connection(
            self.match_server.HOST, self.match_server.PORT)
        # the request message
        message = {
            'from': 'main',
            'operation': 'cancel',
            'player_id': player_id
        }
        await self.sendMessage(writer, message)
        # then wait for reply
        response = await self.receiveMessage(reader)
        response['from'] = 'main'
        # forward result to client
        await self.sendMessage(client_writer, response)


if __name__ == "__main__":
    server = MainServer(config.main_server, config.match_server)
    asyncio.run(server.startServer())

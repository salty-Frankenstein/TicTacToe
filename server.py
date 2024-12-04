import asyncio
import message as msg
import config


class MainServer(msg.MessageServer):
    def __init__(self, address, match_server, game_server) -> None:
        super().__init__(True, address)
        self.match_server = match_server
        self.game_server = game_server
        # mapping from client id to its connection
        self.clients = {}
        # mapping from game id to its connection
        self.games = {}

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

                if message['from'] == 'client':
                    # register a new player
                    client_id = message['id']
                    if client_id not in self.clients.keys():
                        self.clients[client_id] = (reader, writer)

                    if message['operation'] == 'match':
                        await self.requestMatch(writer, client_id)
                    elif message['operation'] == 'cancel':
                        await self.requestCancel(writer, client_id)
                    elif message['operation'] == 'place':
                        x, y = message['x'], message['y']
                        await self.requestPlace(x, y, message['game_id'])

                elif message['from'] == 'game':
                    game_id = message['game_id']
                    if game_id not in self.games.keys():
                        self.games[game_id] = (reader, writer)
                    if message['operation'] == 'move':
                        player1, player2 = message['player1'], message['player2']
                        msg_to_player = {
                            'from': 'main',
                            'status': 'game',
                            'grid': message['grid'],
                            'turn_player': message['turn_player']
                        }
                        # send to both players
                        await self.sendToClient(player1, msg_to_player)
                        await self.sendToClient(player2, msg_to_player)
                    elif message['operation'] == 'finish':
                        msg_to_player = {
                            'from': 'main',
                            'status': 'finish',
                            'winner': message['winner']
                        }
                        # send to both players
                        await self.sendToClient(player1, msg_to_player)
                        await self.sendToClient(player2, msg_to_player)

        except asyncio.IncompleteReadError:
            print(f"Connection closed by {addr}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def sendToClient(self, client_id, message):
        '''
        send message to a client
        '''
        _, writer = self.clients[client_id]
        await self.sendMessage(writer, message)

    async def startGame(self, player1, player2):
        '''
        tell the game server to start a game between player1 & player2
        return the game id of this game
        '''
        reader, writer = await asyncio.open_connection(
            self.game_server.HOST, self.game_server.PORT)
        message = {
            'from': 'main',
            'operation': 'start',
            'player1': player1,
            'player2': player2
        }
        await self.sendMessage(writer, message)
        response = await self.receiveMessage(reader)
        # TODO: check if the response status is OK
        writer.close()
        await writer.wait_closed()
        return response['game_id']

    async def requestPlace(self, x, y, game_id):
        _, writer = self.games[game_id]
        message = {
            'from': 'main',
            'opeation': 'place',
            'x': x,
            'y': y,
            'game_id': game_id
        }
        await self.sendMessage(writer, message)

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
            player1, player2 = response['player_id1'], response['player_id2']
            # tell the game server to start game!
            game_id = await self.startGame(player1, player2)
            # if the game server is ready, tell the clients to get ready
            message = {
                'from': 'main',
                'status': 'match_ready',
                'game_id': game_id,
                'you_are': 1            # player1 or player2
            }
            await self.sendToClient(player1, message)
            # tell player2 as well
            message['you_are'] = 2
            await self.sendToClient(player2, message)
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
    server = MainServer(config.main_server,
                        config.match_server, config.game_server)
    asyncio.run(server.startServer())

import asyncio
import message as msg
import config


class MatchServer(msg.MessageServer):
    '''
    the matching server, responsible for matching players
    '''

    def __init__(self, address, main_server) -> None:
        super().__init__(True, address)
        # the address of main server
        self.main_server = main_server
        self.lock = asyncio.Lock()
        self.first_player = None

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
        addr = writer.get_extra_info('peername')
        print(f"New connection from {addr}")

        try:
            # get message from main server
            message = await self.receiveMessage(reader)

            if message['from'] != 'main':
                # only accept connection from main
                raise  # close this connection
            if message['operation'] == 'match':
                async with self.lock:
                    current_player = message['player_id']
                    # check the current status
                    # or first check if it is the first_player
                    if self.first_player is None or self.first_player == current_player:
                        self.first_player = message['player_id']
                        # no other players
                        response = {
                            'from': 'match',
                            'status': 'wait'
                        }
                        await self.sendMessage(writer, response)
                    else:
                        # finish matching
                        matched_player = self.first_player
                        self.first_player = None
                        response = {
                            'from': 'match',
                            'status': 'ok',
                            'player_id1': message['player_id'],
                            'player_id2': matched_player
                        }
                        await self.sendMessage(writer, response)
            elif message['operation'] == 'cancel':
                # make sure player id is the same
                if self.first_player == message['player_id']:
                    self.first_player = None
                    response = {
                        'from': 'match',
                        'status': 'ok',
                    }
                    await self.sendMessage(writer, response)
                else:
                    # if it is not the current player, then just ignore
                    response = {
                        'from': 'match',
                        'status': 'ignore'
                    }
                    await self.sendMessage(writer, response)
            else:
                # TODO: invalid operation
                pass
        except asyncio.IncompleteReadError:
            print(f"Connection closed by {addr}")
        finally:
            writer.close()
            await writer.wait_closed()


if __name__ == "__main__":
    server = MatchServer(config.match_server, config.main_server)
    asyncio.run(server.startServer())

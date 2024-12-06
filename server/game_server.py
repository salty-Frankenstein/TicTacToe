import asyncio
import message as msg
import config


class Grid:
    def __init__(self) -> None:
        # the gird `0` for none, `1` and `2` for each player
        self.__grid = [[0, 0, 0] for _ in range(3)]

    def isPlayer(self, player):
        return player == 1 or player == 2

    def checkValid(self, x, y):
        return self.__grid[x][y] == 0

    def place(self, x, y, player):
        assert self.isPlayer(player)
        self.__grid[x][y] = player

    def row(self, i):
        assert i >= 0 and i <= 2
        return self.__grid[i]

    def colomn(self, i):
        assert i >= 0 and i <= 2
        return [l[i] for l in self.__grid]

    def diag(self, i):
        if i == 1:
            return [self.__grid[i][i] for i in range(3)]
        elif i == 2:
            return [self.__grid[i][2-i] for i in range(3)]
        else:
            assert 0

    def satisfy(self, row, player):
        assert self.isPlayer(player)
        return all(i == player for i in row)

    def checkWin(self, player):
        assert self.isPlayer(player)
        for i in self.__grid:
            if i == [player] * 3:
                return True
        for i in range(3):
            # check 3 rows and columns
            if self.satisfy(self.row(i), player) or \
               self.satisfy(self.colomn(i), player):
                return True

        if self.satisfy(self.diag(1), player) or \
                self.satisfy(self.diag(2), player):
            return True
        return False

    def checkDraw(self):
        flag = True
        for i in range(3):
            for j in range(3):
                if self.__grid[i][j] == 0:
                    flag = False
        return flag

    def show(self):
        def showChar(i):
            if i == 0:
                return ' '
            elif i == 1:
                return 'O'
            else:
                return 'X'

        res = '-------------\n'
        for i in range(3):
            res += '|'
            for j in range(3):
                res += ' ' + showChar(self.__grid[i][j]) + ' |'
            res += '\n'
            res += '-------------\n'
        return res


class GameServer(msg.MessageServer):
    '''
    the game server, for the main game logic
    '''

    def __init__(self, debug, address, main_server) -> None:
        super().__init__(debug, address)
        self.main_server = main_server
        self.game_id = 0

    async def startServer(self):
        server = await asyncio.start_server(
            self.handleMain, self.address.HOST, self.address.PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server is running on {addr}")

        async with server:
            await server.serve_forever()

    async def playGame(self, player1, player2, game_id):
        reader, writer = await asyncio.open_connection(
            self.main_server.HOST, self.main_server.PORT)

        grid = Grid()
        turn_player = 1
        # the game loop
        while True:
            # the game info this turn
            message = {
                'from': 'game',
                'operation': 'move',
                'game_id': game_id,
                'grid': grid.show(),
                'player1': player1,
                'player2': player2,
                'turn_player': turn_player
            }
            await self.sendMessage(writer, message)
            # perform playes's move, retry until complete
            while True:
                # get player's move
                response = await self.receiveMessage(reader)
                x, y = response['x'], response['y']
                if grid.checkValid(x, y):
                    grid.place(x, y, turn_player)
                    break
                else:
                    # tell the player to place again
                    message = {
                        'from': 'game',
                        'operation': 'retry',
                        'game_id': game_id,
                        'player': turn_player
                    }
                    await self.sendMessage(writer, message)

            # check winning
            if grid.checkWin(turn_player):
                message = {
                    'from': 'game',
                    'game_id': game_id,
                    'grid': grid.show(),
                    'operation': 'finish',
                    'winner': turn_player
                }
                await self.sendMessage(writer, message)
                break
            elif grid.checkDraw():
                message = {
                    'from': 'game',
                    'game_id': game_id,
                    'grid': grid.show(),
                    'operation': 'finish',
                    'winner': 0
                }
                await self.sendMessage(writer, message)
                break

            # change turn
            if turn_player == 1:
                turn_player = 2
            else:
                turn_player = 1

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
            if message['operation'] == 'start':
                player1, player2 = message['player1'], message['player2']
                # create a new game
                self.game_id += 1
                # then the game is ready
                response = {
                    'from': 'game',
                    'status': 'ok',
                    'game_id': self.game_id
                }
                await self.sendMessage(writer, response)
                asyncio.create_task(self.playGame(
                    player1, player2, self.game_id))
            else:
                # TODO: invalid operation
                pass
        except asyncio.IncompleteReadError:
            print(f"Connection closed by {addr}")
        finally:
            writer.close()
            await writer.wait_closed()


if __name__ == "__main__":
    server = GameServer(config.debug, config.game_server, config.main_server)
    asyncio.run(server.startServer())

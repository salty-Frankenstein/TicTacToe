import asyncio
import message as msg
import time
import random
import signal

debug = False


def generate_player_id():
    timestamp = int(time.time() * 1000)
    random_part = random.randint(1000, 9999)
    return f"{timestamp}{random_part}"


async def async_input(prompt):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)


def readXY(s):
    def valid(x):
        return x >= 0 and x <= 2
    try:
        parts = s.split()
        if len(parts) != 2:
            raise ValueError
        a, b = int(parts[0]), int(parts[1])
        if valid(a) and valid(b):
            return a, b
        else:
            raise ValueError
    except ValueError:
        return None


class Client(msg.Message):
    def __init__(self, address) -> None:
        super().__init__(debug)
        # address of server
        self.server = address
        # player id, it should be unique
        self.id = generate_player_id()

    async def start(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.server.HOST, self.server.PORT)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def sendMessage(self, message):
        await super().sendMessage(self.writer, message)

    async def receiveMessage(self):
        return await super().receiveMessage(self.reader)

    async def match(self, event):
        '''
        matching procedure
        '''
        while not event.is_set():
            message = {
                "from": "client",
                "id": self.id,
                "operation": "match"}
            await self.sendMessage(message)
            res = await self.receiveMessage()
            if res['status'] == 'match_ready':
                return res['you_are'], res['game_id']
            elif res['status'] == 'wait':
                await asyncio.sleep(res['time'])
            else:
                assert 0

    async def cancelMatch(self):
        message = {
            "from": "client",
            "id": self.id,
            "operation": "cancel"
        }
        await self.sendMessage(message)
        res = await self.receiveMessage()
        # TODO: check result?

    async def place(self, game_id, player):
        '''
        the procedure for asking player to input and tell the server
        '''
        while True:
            res = await async_input('game> ')
            res = readXY(res)
            if res:
                x, y = res
                response = {
                    'from': 'client',
                    'operation': 'place',
                    'game_id': game_id,
                    'id': self.id,
                    'player': player,
                    'x': x,
                    'y': y
                }
                await self.sendMessage(response)
                break
            else:
                print('invalid move, please input x y')

    async def playGame(self, player, game_id):
        c = 'O' if player == 1 else 'X'
        print('Game started, you are player ' + c)
        while True:
            # wait for a new turn
            message = await self.receiveMessage()
            if message['status'] == 'finish':
                print(message['grid'])
                if message['winner'] == player:
                    print('You win!')
                else:
                    print('You lose.')
                break
            elif message['status'] == 'retry':
                print('Invalid move, please try again.')
                await self.place(game_id, player)
            elif message['status'] != 'game':
                # for some reasons, there could be response from main on the fly
                # for matching's result, although we already entered the game
                # therefore, check the message status first
                pass
            else:
                # normal case
                print(message['grid'])

                if message['turn_player'] == player:
                    # if it's my turn
                    print('You move! Input x y:')
                    await self.place(game_id, player)
                else:
                    # not my turn, just wait for next turn
                    print("opponent's turn, please wait...")

    async def run(self):
        '''
        main logic of client
        '''
        print('client started')
        while True:
            res = await async_input('menu> ')
            if res == 'quit':
                return
            elif res == 'match':
                print('now matching, press Ctrl+C to quit...')
                # this task will wait until finish matching

                stop_event = asyncio.Event()

                def handle_sigint():
                    print("\nCtrl+C received! Stopping...")
                    stop_event.set()

                loop = asyncio.get_event_loop()
                loop.add_signal_handler(signal.SIGINT, handle_sigint)
                task = asyncio.create_task(self.match(stop_event))
                await task
                if task.done():
                    # matched
                    print('matched!')
                    # start game
                    player, game_id = task.result()
                    await self.playGame(player, game_id)
                else:
                    await self.cancelMatch()


async def run():
    client = Client(msg.Address('127.0.0.1', 8000))
    await client.start()
    await client.run()
    await client.close()

if __name__ == "__main__":
    asyncio.run(run())

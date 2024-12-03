import asyncio
import message as msg
import time
import random


def generate_player_id():
    timestamp = int(time.time() * 1000)
    random_part = random.randint(1000, 9999)
    return f"{timestamp}{random_part}"


async def async_input(prompt):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)


class Client(msg.Message):
    def __init__(self, address) -> None:
        super().__init__(True)
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

    async def match(self):
        '''
        matching procedure
        '''
        while True:
            message = {
                "from": "client",
                "id": self.id,
                "operation": "match"}
            await self.sendMessage(message)
            res = await self.receiveMessage()
            if res['status'] == 'ok':
                # TODO: Do ok
                return
            elif res['status'] == 'wait':
                await asyncio.sleep(res['time'])

    async def cancelMatch(self):
        message = {
            "from": "client",
            "id": self.id,
            "operation": "cancel"
        }
        await self.sendMessage(message)
        res = await self.receiveMessage()
        # TODO: check result?

    async def run(self):
        '''
        main logic of client
        '''
        print('client started')
        while True:
            res = await async_input('menu>')
            if res == 'quit':
                return
            elif res == 'match':
                print('now matching:')
                # this task will wait until finish matching
                task = asyncio.create_task(self.match())
                while True:
                    # user can cancel while waiting
                    res = await async_input('match>')
                    if res == 'quit':
                        task.cancel()
                        # ask main server to cancel
                        await self.cancelMatch()
                        break


async def run():
    client = Client(msg.Address('127.0.0.1', 8000))
    await client.start()
    await client.run()
    await client.close()

if __name__ == "__main__":
    asyncio.run(run())

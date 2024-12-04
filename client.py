import asyncio
import message as msg
import time
import random
import signal

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
                return
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
                print('now matching, press Ctrl+C to quit...')
                # this task will wait until finish matching

                stop_event = asyncio.Event()
                
                def handle_sigint():
                    print("\nCtrl+C received! Stopping...")
                    stop_event.set()
                
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(signal.SIGINT, handle_sigint)
                task = asyncio.create_task(self.match(stop_event))  # 创建任务运行无限循环
                await task  # 等待任务运行
                if task.done():
                    # matched
                    print('matched!')
                    pass
                else:
                    await self.cancelMatch()

async def run():
    client = Client(msg.Address('127.0.0.1', 8000))
    await client.start()
    await client.run()
    await client.close()

if __name__ == "__main__":
    asyncio.run(run())

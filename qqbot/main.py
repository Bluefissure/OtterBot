import asyncio
import traceback
import time
import json
import logging
import threading
import yaml
import websockets
import events
from QQBot import QQBot

_log = logging.getLogger()
_log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s -%(levelname)s- %(message)s')
ch.setFormatter(formatter)

_log.addHandler(ch)

BOT_CONFIG = None
with open("config.yaml", "r", encoding='utf-8') as f:
    BOT_CONFIG = yaml.load(f, Loader=yaml.FullLoader)

async def main():
    while True:
        try:
            _log.info("=== OtterBot QQ Bot v0.0.0.1 ===")
            Q = QQBot(BOT_CONFIG)
            Q.subscribe(events)
            await Q.run()
        except Exception as e:
            _log.error(e)
            traceback.print_exc()
            _log.info("Sleeping for 10 seconds...")
            time.sleep(10)


class qqbotThread(threading.Thread):
    def __init__(self, threadID, name, delay=0):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay

    def run(self):
        asyncio.run(main())


if __name__ == '__main__':
    thread1 = qqbotThread(1, "qqbotThread", 0)

    thread1.start()
    thread1.join()

    _log.info("Threads were terminated.")

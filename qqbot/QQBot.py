import logging
import json
import asyncio
import threading
import time
import requests
import websockets
import inspect
from collections import defaultdict
from consts import EVENT_INTENT, ClientState

class QQBot(object):
    def __init__(self, config) -> None:
        self.token = None
        self.expiration = 0
        self.config = config
        self.app_id = str(config['app_id'])
        self.ws = None
        self._s = 0
        self.username = 'Unknown QQBot'
        self.bot = True
        self.version = None
        self.session_id = None
        self.id = None
        self._log = logging.getLogger('QQBot')
        self.http = requests.Session()
        self._heartbeat_thread = None
        self._subscriptions = defaultdict(list)
        self._state = ClientState.INIT
        self._refresh_token()

    def __str__(self) -> str:
        return f'QQBot {self.username}'

    async def run(self):
        reconnect_count = 0
        while reconnect_count < 50:
            try:
                self._log.info('Connecting to QQ...')
                async with websockets.connect("wss://api.sgroup.qq.com/websocket/") as websocket:
                    self.ws = websocket
                    async for message in websocket:
                        jdata = json.loads(message)
                        await self.handle(jdata)
            except websockets.exceptions.ConnectionClosedError:
                self._log.info('Connection closed, try reconnecting...')
                reconnect_count += 1
            except Exception as e:
                raise e


    def _refresh_token(self):
        if time.time() >= self.expiration:
            self._log.info('Refreshing token...')
            self._get_token()
        else:
            self._log.debug('Token still valid, expires in %s seconds', int(self.expiration - time.time()))

    def _get_token(self):
        token_url = "https://bots.qq.com/app/getAppAccessToken"
        response = requests.post(token_url, json={
            "appId": str(self.config['app_id']),
            "clientSecret": str(self.config['app_secret']),
        }, timeout=5)
        self._log.info(response.json())
        self.token = response.json()['access_token']
        self.expiration = time.time() + int(response.json()['expires_in'])
        self._log.info('Token refreshed, expires in %s seconds',
                       response.json()['expires_in'])

    @property
    def intents(self) -> list:
        intents = 0
        sub_keys = self._subscriptions.keys()
        for event in sub_keys:
            intent = EVENT_INTENT.get(event)
            if intent:
                intents |= intent.value
        self._log.debug('Generated intents %s from events: %s', intents, list(sub_keys))
        return intents

    @property
    def base_url(self) -> str:
        return 'https://api.sgroup.qq.com'

    @property
    def headers(self) -> dict:
        return {'Authorization': f'QQBot {self.token}', 'X-Union-Appid': self.app_id}

    @property
    def s(self) -> int:
        return self._s

    @s.setter
    def s(self, value: int):
        self._s = value

    @property
    def log(self):
        return self._log

    async def _heartbeat(self):
        first_hearbeat = True
        while True:
            self._refresh_token()
            await self.ws.send(json.dumps({
                "op": 1,
                "d": self.s if not first_hearbeat else None
            }))
            self._log.debug('%s heartbeat sent.', self)
            first_hearbeat = False
            time.sleep(45)

    def _heartbeat_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._heartbeat())
        loop.close()

    def _spawn_heartbeat(self):
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self._heartbeat_thread.start()

    def _update_info(self, ready_data: dict):
        self.version = ready_data['version']
        self.session_id = ready_data['session_id']
        user = ready_data['user']
        self.id = user['id']
        self.bot = user['bot']
        self.username = user['username']

    def _on_ready(self, ready_data: dict):
        self._state = ClientState.READY
        self._update_info(ready_data)
        self._spawn_heartbeat()

    async def try_login(self):
        self._log.info('Try logging in...')
        await self.ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": f"QQBot {self.token}",
                "intents": self.intents,
                "shard": [0, 1],
            }}))

    async def reconnect(self):
        self._log.info('Try reconnecting...')
        await self.ws.send(json.dumps({
            "op": 6,
            "d": {
                "token": f"QQBot {self.token}",
                "session_id": self.session_id,
                "seq": self.s,
            }}))

    def send_group_message(self, group_id: str, content: str, reply_msg_id: str = "", image: str = None):
        self._log.debug('Sending message %s to group %s...', content, group_id)
        post_data = {
            "content": content,
            "msg_type": 0,
        }
        if reply_msg_id:
            post_data['msg_id'] = reply_msg_id
        self._log.debug('Post data: %s', json.dumps(post_data, indent=2))
        response = requests.post(
            f'{self.base_url}/v2/groups/{group_id}/messages',
            headers=self.headers,
            json=post_data,
            timeout=5,
        )
        self._log.debug('HTTP response: %s', response.text)

    def reply_group_message(self, message:dict, content: str, image: str = None):
        data = message['d']
        group_id = data['group_openid']
        reply_msg_id = data['id']
        self.send_group_message(group_id, content, reply_msg_id)
    
    def send_channel_message(self, channel_id: str, content: str, reply_msg_id=-1, image: str = None):
        self._log.debug('Sending message %s to channel %s...', content, channel_id)
        post_data = {
            "content": content,
        }
        if reply_msg_id != -1:
            post_data['msg_id'] = reply_msg_id
        if image:
            post_data['image'] = image
        response = requests.post(
            f'{self.base_url}/channels/{channel_id}/messages',
            headers=self.headers,
            json=post_data,
            timeout=5,
        )
        self._log.debug('HTTP response: %s', response.text)
    
    def reply_channel_message(self, message:dict, content: str, image: str = None):
        data = message['d']
        channel_id = data['channel_id']
        reply_msg_id = data['id']
        self.send_channel_message(channel_id, content, reply_msg_id)

    async def handle(self, message: dict):
        op = message['op']
        s = message.get('s', -1)
        if self._state == ClientState.READY and s > -1:
            self.s = s
        if op == 10:
            self._log.debug('QQ says hello.')
            if self._state == ClientState.INIT:
                await self.try_login()
            elif self._state == ClientState.RECONNECT:
                await self.reconnect()
        elif op == 7:
            self._log.debug('QQ requires reconnect.')
            self._state = ClientState.RECONNECT
        elif op == 0:
            t = message['t']
            if t == 'READY':
                self._on_ready(message['d'])
                self._log.info('%s is ready.', self)
            elif t == "RESUMED":
                self._state = ClientState.READY
                self._log.info('%s resumed.', self)
            elif t in self._subscriptions:
                for func in self._subscriptions[t]:
                    func(message)
            else:
                self._log.debug(json.dumps(
                    message, indent=2, ensure_ascii=False))
        elif op == 11:
            self._log.debug('%s heartbeat received.', self)
        else:
            self._log.debug(json.dumps(message, indent=2, ensure_ascii=False))


    def _subscribe(self, event: str, func: callable):
        self._subscriptions[event].append(func)
        self._log.debug('Subscribed to event %s.', event)
    

    def subscribe(self, events):
        for event in EVENT_INTENT.keys():
            on_event = f"on_{event.lower()}"
            if hasattr(self, on_event) and hasattr(events, on_event):
                Q_on_event = getattr(self, on_event)
                events_on_event = getattr(events, on_event)
                self._log.info("Subscribing to %s with %s", event, on_event)
                self._subscribe(event, Q_on_event(events_on_event))


    def on_at_message_create(self, func: callable):
        def wrap(*args, **kwargs):
            func_meta = inspect.getfullargspec(func)
            if "qqbot" in func_meta.args:
                kwargs['qqbot'] = self
            func(*args, **kwargs)
        return wrap

    def on_group_at_message_create(self, func: callable):
        def wrap(*args, **kwargs):
            func_meta = inspect.getfullargspec(func)
            if "qqbot" in func_meta.args:
                kwargs['qqbot'] = self
            func(*args, **kwargs)
        return wrap

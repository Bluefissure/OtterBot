import logging
import json
import asyncio
import threading
import time
import requests
import inspect
from collections import defaultdict
from consts import EVENT_INTENT

class QQBot(object):
    def __init__(self, config, ws) -> None:
        self.token = None
        self.expiration = 0
        self.config = config
        self.ws = ws
        self._s = 0
        self.username = 'Unknown QQBot'
        self.bot = True
        self.version = None
        self.session_id = None
        self.id = None
        self.logged_in = False
        self._log = logging.getLogger('QQBot')
        self.http = requests.Session()
        self._heartbeat_thread = None
        self._subscriptions = defaultdict(list)
        self._refresh_token()

    def __str__(self) -> str:
        return f'QQBot {self.username}'

    def _refresh_token(self):
        if time.time() >= self.expiration:
            self._log.info('Refreshing token...')
            self._get_token()

    def _get_token(self):
        token_url = "https://bots.qq.com/app/getAppAccessToken"
        response = requests.post(token_url, json={
            "appId": str(self.config['app_id']),
            "clientSecret": str(self.config['app_secret']),
        }, timeout=5)
        self._log.info(response.json())
        self.token = response.json()['access_token']
        self.expiration = time.time() + int(response.json()['expires_in'])
        self._log.info('Token refreshed, expires in %s',
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
        return 'https://api.sgroup.qq.com/v2'

    @property
    def base_url_channel(self) -> str:
        return 'https://api.sgroup.qq.com'

    @property
    def headers(self) -> dict:
        return {'Authorization': f'QQBot {self.token}', 'X-Union-Appid': "102048867"}

    @property
    def s(self) -> int:
        return self._s

    @property
    def log(self):
        return self._log

    @s.setter
    def s(self, value: int):
        self._s = value


    async def _heartbeat(self):
        first_hearbeat = True
        session_id = self.session_id
        while True:
            if self.session_id != session_id:
                self._log.debug('%s session id changed.', self)
                break
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

    def _logged_in(self, ready_data: dict):
        self.logged_in = True
        self._update_info(ready_data)
        self._spawn_heartbeat()

    async def try_login(self):
        await self.ws.send(json.dumps({
            "op": 2,
            "d": {
                "token": f"QQBot {self.token}",
                "intents": self.intents,
                "shard": [0, 1],
            }}))

    def send_group_message(self, group_id: str, content: str):
        self._log.debug('Sending message %s to group %s...', content, group_id)
        response = requests.post(
            f'{self.base_url}/groups/{group_id}/messages',
            headers=self.headers,
            json={
                "content": content,
                "msg_type": 0,
                "timestamp": int(time.time()),
            },
            timeout=5,
        )
        self._log.debug('HTTP response: %s', response.text)
    
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
            f'{self.base_url_channel}/channels/{channel_id}/messages',
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
        if op == 10:
            self._log.debug('QQ says hello.')
            if not self.logged_in:
                self._log.info('Try logging in...')
                await self.try_login()
        elif op == 0:
            t = message['t']
            self.s = message['s']
            if t == 'READY':
                if not self.logged_in:
                    self._logged_in(message['d'])
                    self._log.info('%s logged in.', self)
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

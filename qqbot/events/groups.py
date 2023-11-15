import json
import re
import requests
import urllib.parse
import os
import logging

_log = logging.getLogger("QQBot Groups")

def on_group_at_message_create(message, qqbot):
    _log.info(json.dumps(message, indent=2, ensure_ascii=False))
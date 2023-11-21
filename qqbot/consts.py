from enum import Enum

class Intent(Enum):
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    DIRECT_MESSAGE = 1 << 12
    OPEN_FORUMS_EVENT = 1 << 18
    AUDIO_OR_LIVE_CHANNEL_MEMBER = 1 << 19
    GROUP_MESSAGES = 1 << 25
    INTERACTION = 1 << 26
    MESSAGE_AUDIT = 1 << 27
    FORUMS_EVENT = 1 << 28
    AUDIO_ACTION = 1 << 29
    PUBLIC_GUILD_MESSAGES = 1 << 30

class IntentOffset(Enum):
    GUILDS = 0
    GUILD_MEMBERS = 1
    GUILD_MESSAGES = 9
    GUILD_MESSAGE_REACTIONS = 10
    DIRECT_MESSAGE = 12
    OPEN_FORUMS_EVENT = 18
    AUDIO_OR_LIVE_CHANNEL_MEMBER = 19
    GROUP_MESSAGES = 25
    INTERACTION = 26
    MESSAGE_AUDIT = 27
    FORUMS_EVENT = 28
    AUDIO_ACTION = 29
    PUBLIC_GUILD_MESSAGES = 30


INTENT_EVENT = {
    Intent.GUILDS: ("GUILD_CREATE", "GUILD_UPDATE", "GUILD_DELETE", "CHANNEL_CREATE", "CHANNEL_UPDATE", "CHANNEL_DELETE"),
    Intent.GUILD_MEMBERS: ("GUILD_MEMBER_ADD", "GUILD_MEMBER_UPDATE", "GUILD_MEMBER_REMOVE"),
    Intent.GUILD_MESSAGES: ("MESSAGE_CREATE", "MESSAGE_DELETE"),
    Intent.GUILD_MESSAGE_REACTIONS: ("MESSAGE_REACTION_ADD", "MESSAGE_REACTION_REMOVE"),
    Intent.DIRECT_MESSAGE: ("DIRECT_MESSAGE_CREATE", "DIRECT_MESSAGE_DELETE"),
    Intent.OPEN_FORUMS_EVENT: ("OPEN_FORUM_THREAD_CREATE", "OPEN_FORUM_THREAD_UPDATE", "OPEN_FORUM_THREAD_DELETE", "OPEN_FORUM_POST_CREATE", "OPEN_FORUM_POST_DELETE", "OPEN_FORUM_REPLY_CREATE", "OPEN_FORUM_REPLY_DELETE"),
    Intent.AUDIO_OR_LIVE_CHANNEL_MEMBER: ("AUDIO_OR_LIVE_CHANNEL_MEMBER_ENTER", "AUDIO_OR_LIVE_CHANNEL_MEMBER_EXIT"),
    Intent.GROUP_MESSAGES: ("GROUP_AT_MESSAGE_CREATE",),
    Intent.INTERACTION: ("INTERACTION_CREATE",),
    Intent.MESSAGE_AUDIT: ("MESSAGE_AUDIT_PASS", "MESSAGE_AUDIT_REJECT"),
    Intent.FORUMS_EVENT: ("FORUM_THREAD_CREATE", "FORUM_THREAD_UPDATE", "FORUM_THREAD_DELETE", "FORUM_POST_CREATE", "FORUM_POST_DELETE", "FORUM_REPLY_CREATE", "FORUM_REPLY_DELETE", "FORUM_PUBLISH_AUDIT_RESULT"),
    Intent.AUDIO_ACTION: ("AUDIO_START", "AUDIO_FINISH", "AUDIO_ON_MIC", "AUDIO_OFF_MIC"),
    Intent.PUBLIC_GUILD_MESSAGES: ("AT_MESSAGE_CREATE", "PUBLIC_MESSAGE_DELETE"),
}

EVENT_INTENT = {}
for k, v in INTENT_EVENT.items():
    for vv in v:
        EVENT_INTENT[vv] = k

class ClientState(Enum):
    INIT = 0
    READY = 1
    RECONNECT = 2
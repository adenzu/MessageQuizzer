from collections import defaultdict
import time
import random

from messagequizzer.db.database import *
from messagequizzer.config import *

short_term_message_memory = []
short_term_author_memory = defaultdict(lambda: None)
short_term_guild_memory = defaultdict(lambda: None)
last_time_written = time.time()


def create_quote(message: Message, author_name: str):
    return f"{message.content}\n-||`{author_name.ljust(32)}`||"


def is_message_qualified(message):
    return (
        not message.author.bot
        and message.content.count(" ") > 1
        and message.content[0].isalpha()
    )


def convert_message(message) -> Message:
    return Message(None, message.author.id, message.guild.id, message.content)


def add_message(message):
    short_term_author_memory[message.author.id] = message.author.display_name
    short_term_message_memory.append(convert_message(message))


def should_write_history():
    return time.time() - last_time_written > DATABASE_UPDATE_COOLDOWN


async def read_history(channel, limit=None):
    after: datetime.datetime = None

    if short_term_guild_memory[channel.guild.id]:
        after = short_term_guild_memory[channel.guild.id]
    else:
        guild = guild_dao.get_guild_by_id(channel.guild.id)
        if guild:
            after = guild.last_read

    async for message in channel.history(limit=limit, after=after):
        if is_message_qualified(message):
            add_message(message)

            if should_write_history():
                await write_history()


async def write_history():
    global last_time_written

    if short_term_message_memory:
        for message in short_term_message_memory:
            message_dao.insert_message(message)
        last_time_written = time.time()


def get_random_message(guild_id):
    message = message_dao.get_random_message_by_server_id(guild_id)
    if message == None:
        message = random.choice(short_term_message_memory)
    if short_term_author_memory[message.author_id]:
        return create_quote(message, short_term_author_memory[message.author_id])
    else:
        author = author_dao.get_author_by_id(message.author_id)
        return create_quote(message, author.display_name)

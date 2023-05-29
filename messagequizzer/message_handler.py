from collections import defaultdict
import time
import random
import functools
import typing
import asyncio
import discord

from messagequizzer.database import *
from messagequizzer.config import *


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


short_term_message_memory = []
short_term_author_memory = defaultdict(lambda: None)
short_term_guild_memory = defaultdict(lambda: None)
last_time_written = 0


def create_quote(message: Message, author_name: str):
    return f"{message.content}\n-||`{author_name.ljust(32)}`||"


def is_message_qualified(message: discord.Message):
    return (
        not message.author.bot
        and message.content.count(" ") > 1
        and message.content[0].isalpha()
    )


def convert_message(message: discord.Message) -> Message:
    return Message(message.id, message.author.id, message.guild.id, message.content)


def get_author(message: discord.Message) -> Author:
    return Author(
        None, message.author.id, message.guild.id, message.author.display_name
    )


def add_message(message: discord.Message) -> None:
    short_term_guild_memory[message.guild.id] = datetime.datetime.now()
    short_term_author_memory[message.author.id] = get_author(message)
    short_term_message_memory.append(convert_message(message))


def should_write_history() -> bool:
    return time.time() - last_time_written > DATABASE_UPDATE_COOLDOWN


async def read_history(channel: discord.TextChannel, limit=None) -> None:
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


async def write_history() -> None:
    global last_time_written

    if short_term_message_memory:
        await message_dao.insert_messages(short_term_message_memory)
        await author_dao.insert_authors(short_term_author_memory.values())
        await guild_dao.insert_guilds(short_term_guild_memory)
        last_time_written = time.time()
        short_term_message_memory.clear()


def get_authors_of_same_guild_except(author: Author):
    authors = author_dao.get_authors_of_same_guild_except(author)
    return authors


def get_random_message(guild_id) -> tuple[Message, Author]:
    message = message_dao.get_random_message_by_server_id(guild_id)
    if message == None:
        message = random.choice(short_term_message_memory)
    if short_term_author_memory[message.author_id]:
        return (message, short_term_author_memory[message.author_id])
    else:
        author = author_dao.get_author_by_id(message.author_id)
        return (message, author)

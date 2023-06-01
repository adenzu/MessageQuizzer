from collections import defaultdict
import time
import random
import discord

from messagequizzer.database import *
from messagequizzer.config import *


short_term_message_memory = defaultdict(list)
short_term_author_memory = {}
short_term_channel_memory = {}
short_term_guild_author_memory = []
last_time_written = time.time()


def is_message_qualified(message: discord.Message):
    return (
        not message.author.bot
        and message.content.count(" ") > 1
        and message.content[0].isalpha()
    )


def convert_message(message: discord.Message) -> Message:
    return Message(message.id, message.author.id, message.guild.id, message.content)


def add_message(message: discord.Message, update_last_read: bool) -> None:
    if update_last_read:
        # problematic
        short_term_channel_memory[message.channel.id] = datetime.datetime.now()
    short_term_author_memory[message.author.id] = message.author.name
    short_term_message_memory[message.guild.id].append(convert_message(message))
    short_term_guild_author_memory.append(
        GuildAuthor(message.guild.id, message.author.id)
    )


def should_write_history() -> bool:
    return time.time() - last_time_written > DATABASE_UPDATE_COOLDOWN


async def read_history(channel: discord.TextChannel, limit=None) -> None:
    after: datetime.datetime = None

    if channel.id in short_term_channel_memory:
        after = short_term_channel_memory[channel.id]
    else:
        channel_db = channel_dao.get_channel_by_id(channel.id)
        if channel_db:
            after = channel_db.last_read
    async for message in channel.history(limit=limit, after=after):
        if is_message_qualified(message):
            add_message(message, True)

            if should_write_history():
                await write_history()
    print(f"Finished reading #{channel.name} of {channel.guild.name}!")

async def get_author_guild_pairs(messages: list[Message]) -> list[tuple[int, int]]:
    return [(message.author_id, message.guild_id) for message in messages]


async def write_history() -> None:
    global last_time_written

    print("Updating the database...")

    for messages in short_term_message_memory.values():
        await message_dao.insert_messages(messages)
        await author_dao.insert_authors(short_term_author_memory)
        await channel_dao.insert_channels(short_term_channel_memory)
        await guild_author_dao.insert_authors_to_guilds(short_term_guild_author_memory)
        last_time_written = time.time()
        short_term_author_memory.clear()
        short_term_channel_memory.clear()

    short_term_message_memory.clear()


def get_author(message: Message) -> Author:
    if message.author_id in short_term_author_memory:
        return Author(message.author_id, short_term_author_memory[message.author_id])
    else:
        return author_dao.get_author_by_id(message.author_id)


def get_random_message(guild_id: int) -> Message:
    message = message_dao.get_random_message_by_guild_id(guild_id)
    if message == None and guild_id in short_term_message_memory:
        message = random.choice(short_term_message_memory[guild_id])
    return message

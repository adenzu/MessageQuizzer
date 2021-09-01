from collections import defaultdict
import linecache
import time
import random


short_term_memory = defaultdict(list)
number_of_messages = defaultdict(int)
last_time_written = time.time()
write_every_seconds = 30
newline_identifier = "752465953.9166822"


def encode_newlines(text):
    return text.replace("\n", newline_identifier)

def decode_newlines(text):
    return text.replace(newline_identifier, "\n")

def is_message_qualified(message):
    return not message.author.bot and message.content.count(" ") > 1 and message.content[0].isalpha()

def create_quote(message):
    return encode_newlines(f"{message.content}\n-||`{message.author.name.ljust(32)}`||") + "\n"

def add_message(message):
    short_term_memory[message.guild.id].append(create_quote(message))

def should_write_history():
    return time.time() - last_time_written > write_every_seconds

async def read_history(channel, limit=None):
    async for message in channel.history(limit=limit):
        if is_message_qualified(message):
            add_message(message)

            if should_write_history():
                await write_history()

async def write_history():
    global last_time_written

    if short_term_memory:
        for guild in short_term_memory:
            number_of_messages[guild] += len(short_term_memory[guild])

            with open(f"messagequizzer/messages/{guild}.txt", "a", encoding="utf-8") as file:
                file.writelines(short_term_memory[guild])

        short_term_memory.clear()
        last_time_written = time.time()
        linecache.updatecache(f"messagequizzer/messages/{guild}.txt")

def get_random_message(guild_id):
    message = "No available message is read yet."

    if number_of_messages[guild_id]:
        quote_index = random.randrange(number_of_messages[guild_id])
        quote = linecache.getline(f"messagequizzer/messages/{guild_id}.txt", quote_index)
        message = decode_newlines(quote)
        print("from file\n", quote, guild_id, quote_index, number_of_messages[guild_id])

    elif short_term_memory[guild_id]:
        message = decode_newlines(random.choice(short_term_memory[guild_id]))
        print("from ram")
    return message

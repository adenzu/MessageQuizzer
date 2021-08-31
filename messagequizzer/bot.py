from messagequizzer.config import *
from messagequizzer.get_messages import get_messages
from messagequizzer.messages import messages

import discord
import random

bot = discord.Client()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    for guild in bot.guilds:
        for channel in guild.channels:
            if str(channel.type) == "text":
                print(channel)
                try:
                    await get_messages(channel, 5000)
                except:
                    pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    elif message.content == COMMAND:
        author = random.choice(list(messages[message.guild]))
        await message.channel.send(random.choice(messages[message.guild][author]) + f"\n-||{author.name}||")
from messagequizzer.config import *
from messagequizzer.message_handler import *

import discord
import random

bot = discord.Client()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}") 
    
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(channel)
            try:
                await read_history(channel)
            except discord.Forbidden:
                pass
            
@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        print(channel)
        try:
            await read_history(channel)
        except discord.Forbidden:
            pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if should_write_history():
        await write_history()

    if is_message_qualified(message):
        add_message(message)
        
    elif message.content == COMMAND:
        await message.channel.send(get_random_message(message.guild.id))

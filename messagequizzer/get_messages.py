from messagequizzer.messages import messages

async def get_messages(channel, limit=None):
    async for message in channel.history(limit=limit):
        if not message.author.bot and message.content.count(" ") > 3 and message.content[0].isalpha():
            (messages[message.guild])[message.author].append(message.content)

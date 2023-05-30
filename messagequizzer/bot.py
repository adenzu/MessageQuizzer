from discord.emoji import Emoji
from discord.enums import ButtonStyle

from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji
from messagequizzer.config import *
from messagequizzer.message_handler import *

import discord
import random

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    print("Catching up!\n")
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"Checking #{channel.name} of {guild.name}")
            try:
                await read_history(channel)
            except discord.Forbidden:
                pass
        print(f"Finished read initialization {guild}!\n")
    print("Finished read initialization!")


@bot.event
async def on_guild_join(guild: discord.Guild):
    for channel in guild.text_channels:
        print(f"Checking #{channel.name} of {guild.name}")
        try:
            await read_history(channel)
        except discord.Forbidden:
            pass
    print(f"Finished read initialization {guild}!")


class QuestionButton(discord.ui.Button):
    def __init__(
        self,
        on_callback,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | Emoji | PartialEmoji | None = None,
        row: int | None = None,
    ):
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )
        self.on_callback = on_callback

    async def callback(self, interaction: Interaction):
        await self.on_callback(self.label, interaction)
        return await super().callback(interaction)


class QuestionView(discord.ui.View):
    def __init__(self, message: Message, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

        self.correct_author = get_author(message)
        self.clicked_users = set()

        authors = guild_author_dao.get_authors_by_guild(message.guild_id)

        authors = [
            author
            for author in authors
            if author.author_id != self.correct_author.author_id
        ]

        chosen_authors = random.sample(authors, k=min(NUMBER_OF_FALSE_ANSWERS, len(authors)))
        chosen_authors.append(self.correct_author)

        random.shuffle(chosen_authors)
        
        for author in chosen_authors:
            self.add_item(QuestionButton(self.on_button_callback, label=author.display_name))

    def set_sent_message(self, message: discord.Message):
        self.sent_message = message

    async def on_timeout(self):
        self.sent_message.edit(f"{self.sent_message.content}\n-||`{self.correct_author.display_name.ljust(MAX_NAME_LENGTH)}`||")
        self.clear_items()
        return await super().on_timeout()

    async def on_button_callback(self, label: str, interaction: Interaction):
        if interaction.user in self.clicked_users:
            await interaction.response.defer()
            return
        self.clicked_users.add(interaction.user)
        if label == self.correct_author.display_name:
            await interaction.response.send_message(
                content=f"You are correct! It was {self.correct_author.display_name}!",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                content=f"It was {self.correct_author.display_name}!", ephemeral=True
            )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if should_write_history():
        await write_history()

    if is_message_qualified(message):
        add_message(message, False)

    elif message.content == COMMAND:
        question_message = get_random_message(message.guild.id)
        if question_message:
            view = QuestionView(question_message)
            sent_message = await message.channel.send(
                content=question_message.content, view=view
            )
            view.set_sent_message(sent_message)
        else:
            await message.channel.send(
                content="The bot still hasn't read this server's messages enough!"
            )

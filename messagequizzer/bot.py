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

    print("Catching up!")
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"Checking #{channel.name} of {guild.name}")
            try:
                await read_history(channel)
            except discord.Forbidden:
                pass


@bot.event
async def on_guild_join(guild: discord.Guild):
    for channel in guild.text_channels:
        print(f"Checking #{channel.name} of {guild.name}")
        try:
            await read_history(channel)
        except discord.Forbidden:
            pass


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
    def __init__(self, correct_author: Author, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

        self.correct_author = correct_author
        self.clicked_users = set()

        other_authors = author_dao.get_authors_of_same_guild_except(correct_author)

        chosen_authors = random.choices(other_authors, k=min(2, len(other_authors)))
        chosen_authors.append(correct_author)

        random.shuffle(chosen_authors)

        for author in chosen_authors:
            self.add_item(QuestionButton(self.test, label=author.display_name))

    async def test(self, label: str, interaction: Interaction):
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
        add_message(message)

    elif message.content == COMMAND:
        question_message, question_message_author = get_random_message(message.guild.id)
        await message.channel.send(
            content=question_message.content, view=QuestionView(question_message_author)
        )

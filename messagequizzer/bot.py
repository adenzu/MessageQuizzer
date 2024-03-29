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
        author: Author,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | Emoji | PartialEmoji | None = None,
        row: int | None = None,
    ):
        if not label:
            label = author.name
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )
        self.author = author
        self.on_callback = on_callback

    async def callback(self, interaction: Interaction):
        await self.on_callback(self.author, interaction)
        return await super().callback(interaction)


class QuestionView(discord.ui.View):
    def __init__(self, message: Message, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)

        self.correct_author = get_author(message)
        self.winners = set()
        self.tries = defaultdict(int)

        authors = guild_author_dao.get_authors_by_guild(message.guild_id)

        authors = [
            author
            for author in authors
            if author.author_id != self.correct_author.author_id
        ]

        chosen_authors = random.sample(
            authors, k=min(NUMBER_OF_FALSE_ANSWERS, len(authors))
        )
        chosen_authors.append(self.correct_author)

        random.shuffle(chosen_authors)

        for author in chosen_authors:
            self.add_item(QuestionButton(self.on_button_callback, author=author))

    def set_sent_message(self, message: discord.Message):
        self.sent_message = message

    async def on_timeout(self):
        await self.sent_message.edit(
            content=f"{self.sent_message.content}\n-||`{self.correct_author.name.ljust(MAX_NAME_LENGTH)}`||",
            view=None,
        )
        return await super().on_timeout()

    async def on_button_callback(
        self, clicked_author: Author, interaction: Interaction
    ):
        if interaction.user in self.winners:
            await interaction.response.defer()
            return
        if clicked_author.name == self.correct_author.name:
            message_content: str
            if interaction.user.id not in self.tries:
                message_content = f"{interaction.user.name} got the answer first try!"
                await player_dao.update_player(interaction.user.id, 1)
            else:
                await player_dao.update_player(
                    interaction.user.id, self.tries[interaction.user.id] + 1
                )
                if self.tries[interaction.user.id] == 1:
                    message_content = (
                        f"{interaction.user.name} got the answer second try!"
                    )
                elif self.tries[interaction.user.id] <= NUMBER_OF_FALSE_ANSWERS:
                    message_content = f"{interaction.user.name} got the answer after {self.tries[interaction.user.id]} tries!"
                else:
                    message_content = f"{interaction.user.name} got the answer after {self.tries[interaction.user.id]} tries..."
            await interaction.response.send_message(
                content=message_content,
            )
            self.winners.add(interaction.user)

        else:
            self.tries[interaction.user.id] += 1
            await mixed_author_dao.increase_mix(
                self.correct_author.author_id, clicked_author.author_id
            )
            await interaction.response.send_message(
                content=f"It was not {clicked_author.name}!", ephemeral=True
            )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if should_write_history():
        await write_history()

    if is_message_qualified(message):
        add_message(message, False)

    if not message.content.startswith("!"):
        return
    elif message.content == GUESS_COMMAND:
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
    elif message.content == SCOREBOARD_COMMAND:
        content = f"# Scoreboard\n`{'Name'.ljust(MAX_NAME_LENGTH)} Avg Guess\n"

        for player in sorted(
            player_dao.get_all_players_by_guild_ascending_by_avg_guess_by_score(
                message.guild.id, 10
            ),
            key=lambda player: player.total_tries / player.score,
        ):
            author = author_dao.get_author_by_id(player.player_id)
            name = author.name
            score = player.total_tries / player.score
            content += f"{name.ljust(MAX_NAME_LENGTH)} {f'{score:.2f}'.rjust(len('Avg Guess'))}\n"

        await message.channel.send(content=content + "`")
    elif message.content == MIXES_COMMAND:
        content = f"# Most Mixed Users\n`{'Correct User'.ljust(MAX_NAME_LENGTH)} {'Guessed User'.ljust(MAX_NAME_LENGTH)} Count\n"

        for mix in sorted(
            mixed_author_dao.get_all_mixes_by_guild_descending_by_times(
                message.guild.id, 10
            ),
            key=lambda mix: mix.times,
        )[::-1]:
            correct_author = author_dao.get_author_by_id(mix.correct_id)
            guessed_author = author_dao.get_author_by_id(mix.guessed_id)
            content += f"{correct_author.name.ljust(MAX_NAME_LENGTH)} {guessed_author.name.ljust(MAX_NAME_LENGTH)} {str(mix.times).rjust(len('Count'))}\n"

        await message.channel.send(content=content + "`")

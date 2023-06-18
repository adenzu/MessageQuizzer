import sqlite3
import datetime
from dataclasses import dataclass


@dataclass
class Message:
    message_id: int
    author_id: int
    guild_id: int
    content: str


@dataclass
class Author:
    author_id: int
    name: str


@dataclass
class Player:
    player_id: int
    score: int
    total_tries: int


@dataclass
class MixedAuthor:
    correct_id: int
    guessed_id: int
    times: int


@dataclass
class TextChannel:
    channel_id: int
    last_read: datetime.datetime


@dataclass
class GuildAuthor:
    guild_id: int
    author_id: int


class MessageDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                author_id INTEGER,
                guild_id INTEGER,
                content TEXT
            )
        """
        )
        self.conn.commit()

    def insert_message(self, message: Message):
        self.cursor.execute(
            "INSERT INTO messages (message_id, author_id, guild_id, content) VALUES (?, ?, ?, ?)",
            (message.message_id, message.author_id, message.guild_id, message.content),
        )
        self.conn.commit()

    async def insert_messages(self, messages: list[Message]):
        values = [
            (message.message_id, message.author_id, message.guild_id, message.content)
            for message in messages
        ]
        self.cursor.executemany(
            "INSERT OR REPLACE INTO messages (message_id, author_id, guild_id, content) VALUES (?, ?, ?, ?)",
            values,
        )
        self.conn.commit()

    def get_random_message_by_guild_id(self, guild_id: int) -> Message:
        self.cursor.execute(
            """
            SELECT * FROM messages
            WHERE guild_id = ?
            ORDER BY RANDOM()
            LIMIT 1
        """,
            (guild_id,),
        )
        row = self.cursor.fetchone()
        if row:
            message = Message(row[0], row[1], row[2], row[3])
            return message
        return None

    def close(self):
        self.cursor.close()
        self.conn.close()


class AuthorDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS authors (
                author_id INTEGER PRIMARY KEY,
                display_name TEXT
            )
        """
        )
        self.conn.commit()

    def insert_author(self, author: Author):
        self.cursor.execute(
            "INSERT OR REPLACE INTO authors (author_id, display_name) VALUES (?, ?)",
            (author.author_id, author.name),
        )
        self.conn.commit()

    async def insert_authors(self, authors: dict[int, str]):
        values = [(id, name) for id, name in authors.items()]
        self.cursor.executemany(
            "INSERT OR REPLACE INTO authors (author_id, display_name) VALUES (?, ?)",
            values,
        )
        self.conn.commit()

    def get_author_by_id(self, author_id) -> Author:
        self.cursor.execute(
            """
            SELECT * FROM authors
            WHERE author_id = ?
        """,
            (author_id,),
        )
        row = self.cursor.fetchone()
        if row:
            author = Author(row[0], row[1])
            return author
        return None

    def close(self):
        self.cursor.close()
        self.conn.close()


class TextChannelDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                last_read TEXT
            )
        """
        )
        self.conn.commit()

    def insert_channel(self, channel: TextChannel):
        self.cursor.execute(
            "INSERT INTO channels (channel_id, last_read) VALUES (?, ?)",
            (channel.channel_id, channel.last_read),
        )
        self.conn.commit()

    async def insert_channels(self, channels: dict[int, datetime.datetime]):
        values = [
            (channel_id, last_read.strftime("%Y-%m-%d %H:%M:%S"))
            for channel_id, last_read in channels.items()
        ]
        self.cursor.executemany(
            "INSERT OR REPLACE INTO channels (channel_id, last_read) VALUES (?, ?)",
            values,
        )
        self.conn.commit()

    def get_channel_by_id(self, channel_id: int) -> TextChannel:
        self.cursor.execute(
            """
            SELECT * FROM channels
            WHERE channel_id = ?
        """,
            (channel_id,),
        )
        row = self.cursor.fetchone()
        if row:
            channel = TextChannel(
                row[0], datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            )
            return channel
        return None

    def close(self):
        self.cursor.close()
        self.conn.close()


class GuildAuthorDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS GuildAuthors (
                guild_id INTEGER,
                author_id INTEGER,
                PRIMARY KEY (guild_id, author_id)
            )
        """
        )
        self.conn.commit()

    def insert_author_to_guild(self, author_id: int, guild_id: int):
        query = "INSERT INTO GuildAuthors (author_id, guild_id) VALUES (?, ?)"
        self.cursor.execute(query, (author_id, guild_id))
        self.conn.commit()

    async def insert_authors_to_guilds(self, pairs: list[GuildAuthor]):
        query = (
            "INSERT OR REPLACE INTO GuildAuthors (author_id, guild_id) VALUES (?, ?)"
        )
        self.cursor.executemany(
            query, [(pair.author_id, pair.guild_id) for pair in pairs]
        )
        self.conn.commit()

    def get_authors_by_guild(self, guild_id: int) -> list[Author]:
        query = """
            SELECT authors.*
            FROM authors
            INNER JOIN GuildAuthors ON authors.author_id = GuildAuthors.author_id
            WHERE GuildAuthors.guild_id = ?
        """
        self.cursor.execute(query, (guild_id,))
        rows = self.cursor.fetchall()
        authors = []
        for row in rows:
            author = Author(row[0], row[1])
            authors.append(author)
        return authors

    def close(self):
        self.cursor.close()
        self.conn.close()


class PlayerDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                score INTEGER,
                total_tries INTEGER
            )
        """
        )
        self.conn.commit()

    def get_all_players_by_guild_ascending_by_avg_guess_by_score(
        self,
        guild_id: int,
        limit: int,
    ) -> list[Player]:
        self.cursor.execute(
            """
            SELECT *
            FROM players p
            INNER JOIN GuildAuthors ga ON p.player_id = ga.author_id
            WHERE ga.guild_id = ?
            ORDER BY p.total_tries/p.score ASC
            LIMIT ?
            """,
            (guild_id, limit),
        )
        rows = self.cursor.fetchall()
        players = []
        for row in rows:
            player = Player(row[0], row[1], row[2])
            players.append(player)
        return players

    def check_player_exists(self, player_id: int) -> bool:
        return self.get_player_by_id(player_id) != None

    def insert_player(self, player: Player):
        self.cursor.execute(
            "INSERT OR REPLACE INTO players (player_id, score, total_tries) VALUES (?, ?, ?)",
            (player.player_id, 1, 1),
        )
        self.conn.commit()

    async def insert_players(self, player_ids: list[int]):
        values = [(id, 1, 1) for id in player_ids]
        self.cursor.executemany(
            "INSERT OR REPLACE INTO players (player_id, score, total_tries) VALUES (?, ?, ?)",
            values,
        )
        self.conn.commit()

    def get_player_by_id(self, player_id: int) -> Player:
        self.cursor.execute(
            """
            SELECT * FROM players
            WHERE player_id = ?
        """,
            (player_id,),
        )
        row = self.cursor.fetchone()
        if row:
            player = Player(row[0], row[1], row[2])
            return player
        return None

    async def update_player(self, player_id: int, try_count: int):
        if self.check_player_exists(player_id):
            self.cursor.execute(
                """
                UPDATE players 
                SET score = score + 1,
                    total_tries = total_tries + ?
                WHERE player_id = ?""",
                (try_count, player_id),
            )
            self.conn.commit()
        else:
            self.insert_player(Player(player_id, 1, try_count))

    async def update_players(self, player_try_pairs: list[tuple[int, int]]):
        values = [(try_count, player_id) for player_id, try_count in player_try_pairs]
        self.cursor.executemany(
            """
            UPDATE players 
            SET score = score + 1,
                total_tries = total_tries + ?
            WHERE player_id = ?""",
            values,
        )
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


class MixedAuthorDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS MixedAuthors (
                correct_id INTEGER,
                guessed_id INTEGER,
                times INTEGER,
                PRIMARY KEY (correct_id, guessed_id)
            )
        """
        )
        self.conn.commit()

    def get_mix_by_ids(self, correct_id: int, guessed_id: int) -> MixedAuthor:
        query = "SELECT * FROM MixedAuthors WHERE correct_id = ? AND guessed_id = ?"
        self.cursor.execute(query, (correct_id, guessed_id))
        row = self.cursor.fetchone()
        if row:
            return MixedAuthor(row[0], row[1], row[2])
        return None

    async def increase_mix(self, correct_id: int, guessed_id: int, increase: int = 1):
        if self.get_mix_by_ids(correct_id, guessed_id):
            query = """
                UPDATE MixedAuthors 
                SET times = times + ?
                WHERE correct_id = ? AND guessed_id = ?
            """
            self.cursor.execute(query, (increase, correct_id, guessed_id))
            self.conn.commit()
        else:
            await self.insert_mix(correct_id, guessed_id, increase)

    def get_all_mixes_by_guild_descending_by_times(
        self,
        guild_id: int,
        limit: int,
    ) -> list[MixedAuthor]:
        self.cursor.execute(
            """
            SELECT *
            FROM MixedAuthors p
            WHERE p.correct_id IN (
                SELECT author_id
                FROM GuildAuthors
                WHERE guild_id = ?
            ) AND p.guessed_id IN (
                SELECT author_id
                FROM GuildAuthors
                WHERE guild_id = ?
            )
            ORDER BY p.times ASC
            LIMIT ?
            """,
            (guild_id, guild_id, limit),
        )
        rows = self.cursor.fetchall()
        mixes = []
        for row in rows:
            player = MixedAuthor(row[0], row[1], row[2])
            mixes.append(player)
        return mixes

    async def insert_mix(self, correct_id: int, guessed_id: int, times: int = 1):
        self.cursor.execute(
            "INSERT OR REPLACE INTO MixedAuthors (correct_id, guessed_id, times) VALUES (?, ?, ?)",
            (correct_id, guessed_id, times),
        )
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


database = "database.db"

message_dao = MessageDAO(database)
message_dao.create_table()

author_dao = AuthorDAO(database)
author_dao.create_table()

channel_dao = TextChannelDAO(database)
channel_dao.create_table()

guild_author_dao = GuildAuthorDAO(database)
guild_author_dao.create_table()

player_dao = PlayerDAO(database)
player_dao.create_table()

mixed_author_dao = MixedAuthorDAO(database)
mixed_author_dao.create_table()

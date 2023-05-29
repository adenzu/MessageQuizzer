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
    id: int
    author_id: int
    guild_id: int
    display_name: str


@dataclass
class Guild:
    guild_id: int
    last_read: datetime.datetime


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
            "INSERT INTO messages (message_id, author_id, guild_id, content) VALUES (?, ?, ?, ?)",
            values,
        )
        self.conn.commit()

    def get_random_message_by_server_id(self, guild_id: int) -> Message:
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
        self.conn.close()


class AuthorDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                guild_id INTEGER,
                display_name TEXT
            )
        """
        )
        self.conn.commit()

    def insert_author(self, author: Author):
        self.cursor.execute(
            "INSERT INTO authors (author_id, guild_id, display_name) VALUES (?, ?, ?)",
            (author.author_id, author.guild_id, author.display_name),
        )
        self.conn.commit()

    def author_exists(self, author_id: int) -> bool:
        self.cursor.execute("SELECT 1 FROM authors WHERE author_id = ?", (author_id,))
        result = self.cursor.fetchone()
        return result is not None

    async def insert_authors(self, authors: list[Author]):
        values = [
            (author.author_id, author.guild_id, author.display_name)
            for author in authors
            if not self.author_exists(author.author_id)
        ]
        self.cursor.executemany(
            "INSERT INTO authors (author_id, guild_id, display_name) VALUES (?, ?, ?)",
            values,
        )
        self.conn.commit()

    def get_authors_of_same_guild_except(self, author: Author) -> list[Author]:
        self.cursor.execute(
            """
            SELECT * FROM authors
            WHERE guild_id = ? AND author_id != ?
        """,
            (author.guild_id, author.author_id),
        )
        rows = self.cursor.fetchall()
        authors = []
        for row in rows:
            author = Author(row[0], row[1], row[2], row[3])
            authors.append(author)
        return authors

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
            author = Author(row[0], row[1], row[2], row[3])
            return author
        return None

    def close(self):
        self.conn.close()


class GuildDAO:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY,
                last_read TEXT
            )
        """
        )
        self.conn.commit()

    def insert_guild(self, guild: Guild):
        self.cursor.execute(
            "INSERT INTO guilds (guild_id, last_read) VALUES (?, ?)",
            (guild.guild_id, guild.last_read),
        )
        self.conn.commit()

    async def insert_guilds(self, guilds: dict[int, datetime.datetime]):
        values = [
            (guild_id, last_read.strftime("%Y-%m-%d %H:%M:%S"))
            for guild_id, last_read in guilds.items()
        ]
        self.cursor.executemany(
            "INSERT OR REPLACE INTO guilds (guild_id, last_read) VALUES (?, ?)",
            values,
        )
        self.conn.commit()

    def get_guild_by_id(self, guild_id: int) -> Guild:
        self.cursor.execute(
            """
            SELECT * FROM guilds
            WHERE guild_id = ?
        """,
            (guild_id,),
        )
        row = self.cursor.fetchone()
        if row:
            guild = Guild(
                row[0], datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            )
            return guild
        return None

    def close(self):
        self.conn.close()


message_dao = MessageDAO("messages.db")
message_dao.create_table()

author_dao = AuthorDAO("authors.db")
author_dao.create_table()

guild_dao = GuildDAO("guilds.db")
guild_dao.create_table()

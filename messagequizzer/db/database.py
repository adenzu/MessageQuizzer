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
    aurhor_id: int
    display_name: str


@dataclass
class Guild:
    guild_id: int
    last_read: datetime.datetime


class MessageDAO:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                author_id INTEGER,
                server_id INTEGER,
                content TEXT
            )
        """
        )
        self.conn.commit()

    def insert_message(self, message: Message):
        self.cursor.execute(
            "INSERT INTO messages (message_id, author_id, server_id, content) VALUES (?, ?, ?, ?)",
            (message.message_id, message.author_id, message.guild_id, message.content),
        )
        self.conn.commit()

    def get_random_message_by_server_id(self, server_id) -> Message:
        self.cursor.execute(
            """
            SELECT * FROM messages
            WHERE server_id = ?
            ORDER BY RANDOM()
            LIMIT 1
        """,
            (server_id,),
        )
        row = self.cursor.fetchone()
        if row:
            message = Message(row[0], row[1], row[2], row[3])
            return message
        return None

    def close(self):
        self.conn.close()


class AuthorDAO:
    def __init__(self, db_name):
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
            "INSERT INTO authors (author_id, display_name) VALUES (?, ?)",
            (author.aurhor_id, author.display_name),
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
            author = Author(row[0], row[1], row[2])
            return author
        return None

    def close(self):
        self.conn.close()


class GuildDAO:
    def __init__(self, db_name):
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

    def insert_(self, guild: Guild):
        self.cursor.execute(
            "INSERT INTO guilds (guild_id, last_read) VALUES (?, ?)",
            (guild.guild_id, guild.last_read),
        )
        self.conn.commit()

    def get_guild_by_id(self, guild_id) -> Guild:
        self.cursor.execute(
            """
            SELECT * FROM guilds
            WHERE guild_id = ?
        """,
            (guild_id,),
        )
        row = self.cursor.fetchone()
        if row:
            author = Author(row[0], row[1], row[2])
            return author
        return None

    def close(self):
        self.conn.close()


message_dao = MessageDAO("messages.db")
message_dao.create_table()

author_dao = AuthorDAO("authors.db")
author_dao.create_table()

guild_dao = GuildDAO("guilds.db")
guild_dao.create_table()

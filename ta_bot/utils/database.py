import sqlite3
from datetime import datetime


class MentorDbConn:

    def __init__(self, dbfile: str):
        self.conn = sqlite3.connect(dbfile)
        self.create_tables()

    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS mentor_channels (
                guild_id    INTEGER,
                channel_id  INTEGER,
                description TEXT,
                PRIMARY KEY (guild_id, channel_id)
            );
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS mentor_users (
                guild_id    INTEGER,
                user_id     INTEGER,
                channel_id  INTEGER,
                queued_time INTEGER,
                is_active   INTEGER,
                PRIMARY KEY (guild_id, user_id)
            );
        ''')

    def get_mentor_channels(self, guild_id: int):
        cursor = self.conn.cursor()
        query = '''
            SELECT channel_id, description FROM mentor_channels
            WHERE guild_id = ?;
        '''
        cursor.execute(query, (guild_id, ))
        return cursor.fetchall()

    def is_mentor_channel(self, guild_id: int, channel_id: int):
        cursor = self.conn.cursor()
        query = '''
            SELECT COUNT(*) FROM mentor_channels
            WHERE guild_id = ? AND channel_id = ?;
        '''
        cursor.execute(query, (guild_id, channel_id))
        return cursor.fetchone()[0] != 0

    def update_mentor_channel(self,
                              guild_id: int,
                              channel_id: int,
                              description: str):
        cursor = self.conn.cursor()
        query = '''
            INSERT OR REPLACE INTO mentor_channels
                (guild_id, channel_id, description)
            VALUES (?, ?, ?);
        '''
        cursor.execute(query, (guild_id, channel_id, description))
        self.conn.commit()
        return cursor.rowcount

    def delete_mentor_channel(self, guild_id: int, channel_id: int):
        cursor = self.conn.cursor()
        query_channels = '''
            DELETE FROM mentor_channels
            WHERE guild_id = ? AND channel_id = ?;
        '''
        cursor.execute(query_channels, (guild_id, channel_id))
        query_users = '''
            DELETE FROM mentor_users
            WHERE guild_id = ? AND channel_id = ?;
        '''
        cursor.execute(query_users, (guild_id, channel_id))
        self.conn.commit()
        return cursor.rowcount

    def get_user_info(self, guild_id: int, user_id: int, fetch_pos: bool):
        '''Finds the channel the given user is currently queued for, whether the
        user is active, and their current position in the queue.'''
        cursor = self.conn.cursor()
        channel_query = '''
            SELECT channel_id, is_active, queued_time FROM mentor_users
            WHERE guild_id = ? AND user_id = ?;
        '''
        cursor.execute(channel_query, (guild_id, user_id))
        if not (result := cursor.fetchone()):
            return (None, None, None) if fetch_pos else (None, None)
        channel_id, is_active, queued_time = result

        if not fetch_pos:
            return channel_id, bool(is_active)

        position_query = '''
            SELECT COUNT(*) FROM mentor_users
            WHERE guild_id = ? AND
                  channel_id = ? AND
                  queued_time <= ?;
        '''
        cursor.execute(position_query, (guild_id, channel_id, queued_time))
        position = cursor.fetchone()[0]
        return channel_id, bool(is_active), position

    def get_users(self, guild_id: int, channel_id: int):
        '''Returns two lists: the active users of a channel, and the users
        currently in the queue.'''
        active, inactive = [], []
        cursor = self.conn.cursor()
        query = '''
            SELECT user_id, is_active FROM mentor_users
            WHERE guild_id = ? AND channel_id = ?
            ORDER BY queued_time ASC;
        '''
        cursor.execute(query, (guild_id, channel_id))
        for user_id, is_active in cursor.fetchall():
            if is_active:
                active.append(user_id)
            else:
                inactive.append(user_id)
        return active, inactive

    def add_user(self, guild_id: int, user_id: int, channel_id: int):
        cursor = self.conn.cursor()
        query = '''
            INSERT INTO mentor_users
                (guild_id, user_id, channel_id, queued_time, is_active)
            VALUES (?, ?, ?, ?, 0);
        '''
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        cursor.execute(query, (guild_id, user_id, channel_id, timestamp))
        self.conn.commit()
        return cursor.rowcount

    def make_active(self, guild_id: int, user_id: int, is_active: bool=True):
        cursor = self.conn.cursor()
        query = '''
            UPDATE mentor_users
            SET is_active = ?
            WHERE guild_id = ? AND user_id = ?;
        '''
        cursor.execute(query, (is_active, guild_id, user_id))
        self.conn.commit()
        return cursor.rowcount

    def delete_user(self, guild_id: int, user_id: int):
        cursor = self.conn.cursor()
        query = '''
            DELETE FROM mentor_users
            WHERE guild_id = ? AND user_id = ?;
        '''
        cursor.execute(query, (guild_id, user_id))
        self.conn.commit()
        return cursor.rowcount

    def get_active_users(self, guild_id: int, channel_id: int):
        cursor = self.conn.cursor()
        query = '''
            SELECT user_id FROM mentor_users
            WHERE guild_id = ? AND
                  channel_id = ? AND
                  is_active = 1;
        '''
        cursor.execute(query, (guild_id, channel_id))
        return [row[0] for row in cursor.fetchall()]

    def get_next_user(self, guild_id: int, channel_id: int):
        cursor = self.conn.cursor()
        query = '''
            SELECT user_id FROM mentor_users
            WHERE guild_id = ? AND
                  channel_id = ? AND
                  is_active = 0
            ORDER BY queued_time ASC
            LIMIT 1;
        '''
        cursor.execute(query, (guild_id, channel_id))
        if (result := cursor.fetchone()):
            return result[0]
        return None

    def skip_user(self, guild_id: int, user_id: int):
        channel_id, is_active = self.get_user_info(guild_id, user_id, False)
        if not channel_id or is_active:
            return

        cursor = self.conn.cursor()
        query = '''
            UPDATE mentor_users
            SET queued_time = ?
            WHERE guild_id = ? AND user_id = ?;
        '''
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        cursor.execute(query, (timestamp, guild_id, user_id))
        self.conn.commit()

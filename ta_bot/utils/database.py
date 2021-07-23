import sqlite3


class MentorDbConn:

    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.create_tables()


    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS mentor_channels (
                guild_id    INTEGER,
                channel_id  INTEGER,
                role_id     INTEGER,
                description TEXT,
                user_limit  INTEGER,
                PRIMARY KEY (guild_id, channel_id)
            );
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS mentor_tas (
                channel_id  INTEGER,
                ta_user_id  INTEGER,
                PRIMARY KEY (channel_id, ta_user_id),
                FOREIGN KEY (channel_id) REFERENCES mentor_channels(channel_id)
            );
        ''')
        # channel ID -1 means any channel
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS mentor_users (
                user_id     INTEGER,
                guild_id    INTEGER,
                channel_id  INTEGER,
                queued_time INTEGER,
                PRIMARY KEY (user_id, guild_id)
            );
        ''')

    def channel_queued(user_id, guild_id):
        '''Finds the channel the given user is currently queued for, or None.
        Note: If the resulting channel ID is not a valid mentoring channel,
        then the fetched row gets removed and it returns None!'''
        channel_query = '''
            SELECT channel_id FROM mentor_users
            WHERE user_id = ? AND guild_id = ?;
        '''
        self.conn.execute(channel_query, (user_id, guild_id))
        if (result := self.conn.fetchone()).rowcount == 0:
            return None
        channel_id = result[0]

        is_valid_query = '''
            SELECT COUNT(*) FROM mentor_channels
            WHERE guild_id = ? AND channel_id = ?;
        '''
        self.conn.execute(is_valid_query, (guild_id, channel_id))
        if self.conn.fetchone()[0] != 0:
            return channel_id

        delete_stmt = '''
            DELETE FROM mentor_users
            WHERE user_id = ? AND guild_id = ?;
        '''
        self.conn.execute(delete_stmt, (user_id, guild_id))
        self.conn.commit()
        return None

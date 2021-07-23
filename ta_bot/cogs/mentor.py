import asyncio
from typing import Optional

import discord
from discord.ext import commands

from ..utils.database import MentorDbConn


class MentorCog(commands.Cog, name='Mentor'):
    '''A cog for TA mentoring'''

    def __init__(self, bot):
        self.bot = bot
        self.db = MentorDbConn('database/mentors.sqlite3')

    @commands.group(brief='Accessing TA mentoring',
                    invoke_without_command=True,
                    aliases=['m'])
    async def mentor(self, ctx: commands.Context):
        '''Access TA's mentoring channels.'''
        await ctx.send_help('mentor')

    @mentor.command(brief='List mentor channels and TAs',
                    aliases=['ls'])
    @commands.guild_only()
    async def list(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        '''Get the list of mentoring channels.'''
        pass

    @mentor.command(brief='Queue for access',
                    aliases=['q'])
    @commands.guild_only()
    async def queue(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        '''Register for a TA's mentor queue.'''
        pass


def setup(bot):
    bot.add_cog(MentorCog(bot))

from copy import copy

import discord
from discord.ext import commands


class UtilsCog(commands.Cog, name='Utils'):
    '''Some bot utilities'''

    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(brief='Pings the bot')
    async def ping(self, ctx):
        '''Get the latency of the bot'''
        latency_ms = self.bot.latency * 1000
        await ctx.send(f'Pong! {latency_ms:.1f} ms')


def setup(bot):
    bot.add_cog(UtilsCog(bot))

from copy import copy

import discord
from discord.ext import commands


class UtilsCog(commands.Cog, name='Utils'):
    '''Some bot utilities'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sudo(self,
                   ctx: commands.Context,
                   user: discord.Member,
                   *,
                   command: str):
        '''Execute a command as another user'''
        new_message = copy(ctx.message)
        new_message.author = user
        new_message.content = ctx.prefix + command
        await self.bot.process_commands(new_message)

    @commands.command(brief='Pings the bot')
    async def ping(self, ctx):
        '''Get the latency of the bot'''
        latency_ms = self.bot.latency * 1000
        await ctx.send(f'Pong! {latency_ms:.1f} ms')


def setup(bot):
    bot.add_cog(UtilsCog(bot))

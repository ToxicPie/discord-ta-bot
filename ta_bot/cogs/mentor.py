import asyncio
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import ComponentContext, SlashContext
from discord_slash.utils.manage_components import (create_button,
                                                   create_actionrow,
                                                   create_select_option,
                                                   create_select)
from discord_slash.utils.manage_commands import create_option
from discord_slash.model import ButtonStyle, SlashCommandOptionType

from ..utils.database import MentorDbConn


class MentorCog(commands.Cog, name='Mentor'):
    '''A cog for TA mentoring'''

    def __init__(self, bot):
        self.bot = bot
        self.db = MentorDbConn('database/mentors.sqlite3')

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        pass

    @cog_ext.cog_slash(name='mentor',
                       description='Access TA mentoring')
    async def mentor(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='join',
                            description='Select a TA\'s channel and '
                                        'join the queue')
    async def mentor_join(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='leave',
                            description='Leave a channel or queue')
    async def mentor_leave(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='query',
                            description='Query your current status')
    async def mentor_query(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='setup',
                            description='Manages the current channel')
    @commands.has_permissions(manage_channels=True)
    async def mentor_setup(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='ls',
                            description='List users in all channels/queues'
                                        'or in a given channel/queue',
                            options=[
                                create_option(
                                    name='channel',
                                    description='The channel to list users in',
                                    option_type=SlashCommandOptionType.CHANNEL,
                                    required=False
                                )
                            ])
    @commands.has_permissions(manage_channels=True)
    async def mentor_ls(self, ctx: SlashContext, channel: discord.TextChannel):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='rm',
                            description='Remove a user from a queue',
                            options=[
                                create_option(
                                    name='user',
                                    description='The user to remove',
                                    option_type=SlashCommandOptionType.USER,
                                    required=True
                                )
                            ])
    @commands.has_permissions(manage_channels=True)
    async def mentor_rm(self, ctx: SlashContext, user: discord.Member):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='finish',
                            description='Finish the current mentoring session')
    @commands.has_permissions(manage_channels=True)
    async def mentor_finish(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='next',
                            description='Invite the next user in the queue')
    @commands.has_permissions(manage_channels=True)
    async def mentor_next(self, ctx: SlashContext):
        pass


def setup(bot):
    bot.add_cog(MentorCog(bot))

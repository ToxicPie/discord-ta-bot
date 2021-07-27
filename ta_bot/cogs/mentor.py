import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import ComponentContext, SlashContext
from discord_slash.utils.manage_components import (create_button,
                                                   create_actionrow,
                                                   create_select_option,
                                                   create_select)
from discord_slash.model import (ButtonStyle,
                                 SlashCommandOptionType,
                                 ComponentType)
from discord_slash.utils.manage_commands import create_option

from ..utils.database import MentorDbConn
from ..utils.discord_embeds import *


class MentorCog(commands.Cog, name='Mentor'):
    '''A cog for TA mentoring'''

    def __init__(self, bot):
        self.bot = bot
        self.db = MentorDbConn('database/mentors.sqlite3')
        self.locks = {}

    def disabled_components(self, components: list[dict]):
        result = []
        for action_row in components:
            new_comps = []
            for component in action_row['components']:
                disabled_comp = component
                disabled_comp['disabled'] = True
                new_comps.append(disabled_comp)
            result.append(create_actionrow(*new_comps))
        return result

    async def disable_all_components(self, ctx: ComponentContext):
        components = self.disabled_components(ctx.origin_message.components)
        await ctx.edit_origin(content=ctx.origin_message.content,
                              components=components)

    def check_and_get_channel(self, ctx: commands.Context, channel_id: int):
        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            # check if it's a valid TA channel
            if (not channel or
                not self.db.is_mentor_channel(ctx.guild.id, channel_id)):
                self.db.delete_user(ctx.guild.id, ctx.author.id)
                channel = None
        else:
            channel = None
        return channel

    async def setup_update(self, ctx: ComponentContext):
        query = await ctx.send('Type the description for this channel, or '
                               '`^C` to cancel:',
                               hidden=True)
        try:
            def check_reply(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            reply = await self.bot.wait_for('message',
                                            check=check_reply,
                                            timeout=60)
            await reply.delete()
            if reply.content.strip().upper() == '^C':
                await ctx.send('Operation cancelled.', hidden=True)
            else:
                description = discord.utils.escape_markdown(
                    discord.utils.escape_mentions(reply.content)
                )
                self.db.update_mentor_channel(ctx.guild.id,
                                              ctx.channel.id,
                                              description)
                embed = embed_success(
                    'This channel has been updated',
                    f'{ctx.channel.mention} is now a TA mentor channel '
                    f'with the description `{description}`.'
                )
                embed.set_footer(
                    text='Make sure you have set the correct '
                         'channel permissions!'
                )
                await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await ctx.send('Operation cancelled.', hidden=True)

    async def setup_delete(self, ctx: ComponentContext):
        self.db.delete_mentor_channel(ctx.guild.id, ctx.channel.id)
        await ctx.send(embed=embed_success(
            'This channel has been updated',
            f'{ctx.channel.mention} is no longer a TA mentor channel.'
        ))

    async def setup_cancel(self, ctx: ComponentContext):
        await ctx.edit_origin(content='Operation cancelled.',
                              components=[])

    async def join_queue(self, ctx: ComponentContext):
        channel_id = int(ctx.selected_options[0].removeprefix('join-'))
        channel = ctx.guild.get_channel(channel_id)
        if (not channel or
            not self.db.is_mentor_channel(ctx.guild.id, channel_id)):
            await ctx.send(embed=embed_error(
                'Invalid channel',
                'The option you selected is no longer a valid TA channel.'
            ))
            return

        qu_channel_id, is_active = self.db.get_user_info(ctx.guild.id,
                                                         ctx.author.id,
                                                         False)
        qu_channel = self.check_and_get_channel(ctx, qu_channel_id)

        if qu_channel:
            await ctx.send(
                embed=embed_error(
                    'Error',
                    f'You are already in the queue of {qu_channel.mention} or '
                    'are already active there.'
                ),
                hidden=True
            )
            return

        self.db.add_user(ctx.guild.id, ctx.author_id, channel_id);
        embed = embed_success(
            'Successfully joined',
            f'You have joined the queue for {channel.mention}.'
        )
        embed.set_footer(
            text='Hint: Use `/mentor query` to view your status.'
        )
        await ctx.send(embed=embed, hidden=True)

    async def next_join(self, ctx: ComponentContext, user_id: int, ta_id: int):
        if ctx.author.id == user_id:
            user = await ctx.guild.fetch_member(user_id)
            self.db.make_active(ctx.guild.id, user_id)
            await ctx.channel.set_permissions(user, send_messages=True)
            await self.disable_all_components(ctx)
            await ctx.send(embed=embed_success(
                'Active user',
                f'{user.mention} has joined the channel.'
            ))
        else:
            # ACK the interaction and silently ignore
            await ctx.defer(edit_origin=True)

    async def next_skip(self, ctx: ComponentContext, user_id: int, ta_id: int):
        if ctx.author.id == user_id or ctx.author.id == ta_id:
            user = await ctx.guild.fetch_member(user_id)
            self.db.skip_user(ctx.guild.id, user_id)
            await ctx.channel.set_permissions(user, overwrite=None)
            await self.disable_all_components(ctx)
            await ctx.send(embed=embed_success(
                'User skipped',
                f'{user.mention} has been moved to the end of the queue.'
            ))
        else:
            # ACK the interaction and silently ignore
            await ctx.defer(edit_origin=True)

    async def next_cancel(self,
                          ctx: ComponentContext,
                          user_id: int,
                          ta_id: int):
        if ctx.author.id == ta_id:
            user = await ctx.guild.fetch_member(user_id)
            await ctx.channel.set_permissions(user, overwrite=None)
            await ctx.edit_origin(content='Operation cancelled.',
                                  components=[])
        else:
            # ACK the interaction and silently ignore
            await ctx.defer(edit_origin=True)

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        lock = self.locks.get(ctx.guild.id)
        if not lock:
            lock = self.locks[ctx.guild.id] = asyncio.Lock()

        async with lock:
            if ctx.component_type == ComponentType.button:
                if ctx.component_id == 'setup-update':
                    await self.setup_update(ctx)
                elif ctx.component_id == 'setup-delete':
                    await self.setup_delete(ctx)
                elif ctx.component_id == 'setup-cancel':
                    await self.setup_cancel(ctx)

                if ctx.component_id.startswith('next'):
                    button_id, user_id, ta_id = ctx.component_id.split(':')
                    user_id , ta_id = int(user_id), int(ta_id)
                    if button_id == 'next-join':
                        await self.next_join(ctx, user_id, ta_id)
                    elif button_id == 'next-skip':
                        await self.next_skip(ctx, user_id, ta_id)
                    elif button_id == 'next-cancel':
                        await self.next_cancel(ctx, user_id, ta_id)

            elif ctx.component_type == ComponentType.select:
                if ctx.component_id == 'join-select':
                    await self.join_queue(ctx)

    @cog_ext.cog_slash(name='mentor',
                       description='Access TA mentoring')
    async def mentor(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(base='mentor',
                            name='join',
                            description='Select a TA mentor channel and '
                                        'join the queue')
    async def mentor_join(self, ctx: SlashContext):
        channel_list = [
            create_select_option(label=f'#{ctx.guild.get_channel(cid).name}',
                                 value=f'join-{cid}',
                                 description=desc)
            for cid, desc in self.db.get_mentor_channels(ctx.guild.id)
        ]
        if not channel_list:
            await ctx.send(
                embed=embed_warning(
                    'No channels',
                    'There are no TA channels for you to join.'
                ),
                hidden=True
            )
            return

        channel_menu = create_select(
            options=channel_list,
            min_values=1,
            max_values=1,
            custom_id='join-select'
        )
        action_row = create_actionrow(channel_menu)
        await ctx.send('Select a TA channel to join:',
                       components=[action_row],
                       hidden=True)

    @cog_ext.cog_subcommand(base='mentor',
                            name='leave',
                            description='Leave a channel or queue')
    async def mentor_leave(self, ctx: SlashContext):
        channel_id, is_active = self.db.get_user_info(ctx.guild.id,
                                                      ctx.author.id,
                                                      False)
        channel = self.check_and_get_channel(ctx, channel_id)

        if not channel:
            result = embed_error(
                'Error',
                'You are not currently in any TA channel or queue!'
            )

        else:
            self.db.delete_user(ctx.guild.id, ctx.author.id)
            await channel.set_permissions(ctx.author, overwrite=None)
            if is_active:
                result = embed_success(
                    'Left active channel',
                    f'You left the TA channel {channel.mention}.'
                )
            else:
                result = embed_success(
                    'Left queue',
                    f'You left the queue for {channel.mention}.'
                )

        result.set_footer(text='Hint: Use `/mentor join` to join a channel.')
        await ctx.send(embed=result, hidden=True)

    @cog_ext.cog_subcommand(base='mentor',
                            name='query',
                            description='Query your current status')
    async def mentor_query(self, ctx: SlashContext):
        channel_id, is_active, position = self.db.get_user_info(ctx.guild.id,
                                                                ctx.author.id,
                                                                True)
        channel = self.check_and_get_channel(ctx, channel_id)

        if not channel:
            result = embed_info(
                'Idle user',
                'You are not currently in any TA channel or queue!'
            )
            result.set_footer(text='Hint: Use `/mentor join` to join one.')

        elif is_active:
            result = embed_info(
                'Active user',
                f'You are currently active in {channel.mention}.'
            )
            result.set_footer(text='Hint: Use `/mentor leave` to leave.')

        else:
            result = embed_info(
                'In queue',
                f'You have requested to join {channel.mention}. '
                f'You are currently position #{position} in the queue.'
            )
            result.set_footer(text='Hint: Use `/mentor leave` to leave.')

        await ctx.send(embed=result, hidden=True)

    @cog_ext.cog_subcommand(base='mentor',
                            name='setup',
                            description='Manages the current channel')
    @commands.has_permissions(manage_channels=True)
    async def mentor_setup(self, ctx: SlashContext):
        if self.db.is_mentor_channel(ctx.guild.id, ctx.channel.id):
            text = ('This channel is already a TA mentoring channel.\n'
                    'What would you like to do?')
            update_btn = create_button(label='Update',
                                       style=ButtonStyle.primary,
                                       custom_id='setup-update')
            delete_btn = create_button(label='Delete',
                                       style=ButtonStyle.danger,
                                       custom_id='setup-delete')
            cancel_btn = create_button(label='Cancel',
                                       style=ButtonStyle.secondary,
                                       custom_id='setup-cancel')
            action_row = create_actionrow(update_btn, delete_btn, cancel_btn)

        else:
            text = ('This channel is not a TA mentoring channel.\n'
                    'Would you like to make it one?')
            create_btn = create_button(label='Yes',
                                       style=ButtonStyle.success,
                                       custom_id='setup-update')
            cancel_btn = create_button(label='No',
                                       style=ButtonStyle.secondary,
                                       custom_id='setup-cancel')
            action_row = create_actionrow(create_btn, cancel_btn)

        await ctx.send(text,
                       components=[action_row],
                       hidden=True)

    @cog_ext.cog_subcommand(base='mentor',
                            name='ls',
                            description='List users in a given channel/queue',
                            options=[
                                create_option(
                                    name='channel',
                                    description='The channel to list users in. '
                                                'Defaults to the current one.',
                                    option_type=SlashCommandOptionType.CHANNEL,
                                    required=False
                                )
                            ])
    @commands.has_permissions(manage_channels=True)
    async def mentor_ls(self,
                        ctx: SlashContext,
                        channel: discord.TextChannel=None):
        if not channel:
            channel = ctx.channel
        if not isinstance(channel, discord.TextChannel):
            raise commands.BadArgument(f'#{channel} is not a valid channel.')

        if not self.db.is_mentor_channel(ctx.guild.id, channel.id):
            warning = embed_warning(
                'Invalid channel',
                f'{channel.mention} is not a mentoring channel.'
            )
            warning.set_footer(text='Hint: Use `/mentor setup` to configure.')
            await ctx.send(embed=warning, hidden=True)
        else:
            async def get_usernames(user_ids):
                for user_id in user_ids:
                    if (user := await ctx.guild.fetch_member(user_id)):
                        yield user.mention
                    else:
                        yield f'*(Invalid user {user_id})*'

            active, inactive = self.db.get_users(ctx.guild.id, channel.id)
            active_list = '\n'.join(
                [name async for name in get_usernames(active)]
            ) or '(No users)'
            inactive_list = '\n'.join(
                [name async for name in get_usernames(inactive)]
            ) or '(No users)'
            embed = embed_info('User list', '')
            embed.add_field(name='Active', value=active_list, inline=True)
            embed.add_field(name='Queued', value=inactive_list, inline=True)
            embed.set_footer(text='Hint: use `/mentor rm` to remove a user.')
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base='mentor',
                            name='rm',
                            description='Remove a user from a channel '
                                        'or queue',
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
        channel_id, is_active = self.db.get_user_info(ctx.guild.id,
                                                      user.id,
                                                      False)
        channel = self.check_and_get_channel(ctx, channel_id)

        if not channel:
            await ctx.send(
                embed=embed_error(
                    'Error',
                    f'{user.mention} is not currently in any channel or queue.'
                ),
                hidden=True
            )
            return

        self.db.delete_user(ctx.guild.id, user.id)
        await channel.set_permissions(user, overwrite=None)

        if is_active:
            result = embed_success(
                'User removed',
                f'{user.mention} was removed from {channel.mention}.'
            )
        else:
            result = embed_success(
                'User removed',
                f'{user.mention} was de-queued for {channel.mention}.'
            )

        await ctx.send(embed=result)

    @cog_ext.cog_subcommand(base='mentor',
                            name='finish',
                            description='Finish the current mentoring session')
    @commands.has_permissions(manage_channels=True)
    async def mentor_finish(self, ctx: SlashContext):
        active_users = self.db.get_active_users(ctx.guild.id, ctx.channel.id)
        if not active_users:
            await ctx.send(
                embed=embed_warning(
                    'No active users',
                    'There are no active users in this channel!'
                ),
                hidden=True
            )
            return

        for user_id in active_users:
            self.db.delete_user(ctx.guild.id, user_id)
            user = await ctx.guild.fetch_member(user_id)
            if user:
                await ctx.channel.set_permissions(user, overwrite=None)

        await ctx.send(embed=embed_success(
            'Mentoring session ended',
            f'{len(active_users)} active users were removed from this channed.'
        ))

    @cog_ext.cog_subcommand(base='mentor',
                            name='next',
                            description='Invite the next user in the queue')
    @commands.has_permissions(manage_channels=True)
    async def mentor_next(self, ctx: SlashContext):
        user_id = self.db.get_next_user(ctx.guild.id, ctx.channel.id)
        if not user_id:
            await ctx.send(
                embed=embed_info(
                    'Empty queue',
                    'There are no users in the queue for this channel!'
                ),
                hidden=True
            )
            return

        user = await ctx.guild.fetch_member(user_id)
        if not user:
            self.db.delete_user(ctx.guild.id, user_id)
            embed = embed_error(
                'Invalid user',
                'The next user in the queue is not a valid member. '
                'They have been removed from the queue.'
            )
            await ctx.send(embed=embed, hidden=True)
            return

        await ctx.channel.set_permissions(user, read_messages=True)
        text = (f'{user.mention}, it\'s your turn to join this channel!\n'
                'Please select an option:')
        button_ids = f':{user.id}:{ctx.author.id}'
        join_btn   = create_button(label='Join',
                                   style=ButtonStyle.success,
                                   custom_id='next-join' + button_ids)
        skip_btn   = create_button(label='Skip',
                                   style=ButtonStyle.danger,
                                   custom_id='next-skip' + button_ids)
        action_row1 = create_actionrow(join_btn, skip_btn)
        cancel_btn = create_button(label='Cancel (TA)',
                                   style=ButtonStyle.secondary,
                                   custom_id='next-cancel' + button_ids)
        action_row2 = create_actionrow(cancel_btn)

        await ctx.send(text, components=[action_row1, action_row2])


def setup(bot):
    bot.add_cog(MentorCog(bot))

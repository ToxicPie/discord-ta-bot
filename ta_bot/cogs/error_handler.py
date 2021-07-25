import logging
import traceback

from discord.ext import commands
from discord_slash.context import InteractionContext
from discord_slash.error import SlashCommandError

from ..utils import discord_embeds


class ErrorHandlerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.bot.add_listener(self.on_error, name='on_command_error')
        self.bot.add_listener(self.on_error, name='on_slash_command_error')

    async def on_error(self, ctx, exception: Exception):

        async def send_error(title, desc):
            error_embed = discord_embeds.embed_error(str(title), str(desc))
            if isinstance(ctx, InteractionContext):
                await ctx.send(embed=error_embed, hidden=True)
            else:
                await ctx.send(embed=error_embed)

        if isinstance(exception, commands.CommandNotFound):
            await send_error('Command not found', exception)

        elif isinstance(exception, (commands.MissingPermissions,
                                    commands.MissingRole)):
            await send_error('Forbidden', exception)

        elif isinstance(exception, commands.UserInputError):
            await send_error('Failed to invoke command', exception)

        elif isinstance(exception, commands.CheckFailure):
            await send_error('Command failed',
                             'Some conditions were not satisfied.')

        elif isinstance(exception, (commands.CommandError,
                                    SlashCommandError)):
            await send_error('Command failed',
                             'An unexpected error happened.')

        try:
            raise exception
        except Exception as ex:
            self.logger.error('Caught exception in command {}: {}\n{}'.format(
                              ctx.command,
                              ex.with_traceback(ex.__traceback__),
                              traceback.format_exc()))


def setup(bot):
    bot.add_cog(ErrorHandlerCog(bot))

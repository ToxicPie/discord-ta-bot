import logging
import traceback
from discord.ext import commands

from . import discord_utils


async def command_error_handler(ctx: commands.Context, exception: Exception):

    async def send_error(title, desc):
        await ctx.send(embed=discord_utils.embed_error(str(title), str(desc)))

    if isinstance(exception, commands.CommandNotFound):
        await send_error('Command not found', exception)

    elif isinstance(exception, (commands.MissingPermissions,
                                commands.MissingRole)):
        await send_error('Command failed', exception)

    elif isinstance(exception, commands.UserInputError):
        await send_error('Failed to invoke command', exception)

    elif isinstance(exception, commands.CheckFailure):
        await send_error('Command failed',
                         'Some conditions were not satisfied.')

    elif isinstance(exception, commands.CommandError):
        await send_error('Command failed',
                         'An unexpected error happened.')

    try:
        raise exception
    except Exception as ex:
        ctx.bot.logger.error('Caught exception in command {}: {}\n{}'.format(
                             ctx.command,
                             ex.with_traceback(ex.__traceback__),
                             traceback.format_exc()))


def setup(bot):
    bot.logger = logging.getLogger(__name__)
    bot.add_listener(command_error_handler, name='on_command_error')

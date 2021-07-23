import discord
from discord.ext import commands
from discord_components import DiscordComponents


def setup_bot(prefix, intents=discord.Intents.default()):
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix),
                       intents=intents)
    DiscordComponents(bot)

    bot.load_extension(f'ta_bot.utils.error_handler')
    bot.load_extension(f'ta_bot.cogs.mentor')

    return bot

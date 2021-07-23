import pathlib

import discord
from discord.ext import commands
from discord_components import DiscordComponents


def setup_bot(prefix, intents=discord.Intents.default()):
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix),
                       intents=intents)
    DiscordComponents(bot)

    cogs = [file.stem for file in pathlib.Path('ta_bot/cogs/').glob('*.py')]
    for cog in cogs:
        bot.load_extension(f'ta_bot.cogs.{cog}')

    return bot

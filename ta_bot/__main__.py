import os

from . import setup_bot


bot_token = os.environ.get('DISCORD_BOT_TOKEN')
bot_prefix = os.environ.get('COMMAND_PREFIX')

bot = setup_bot(bot_prefix)

bot.run(bot_token)

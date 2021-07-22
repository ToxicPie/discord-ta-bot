import discord


def embed_error(title, desc):
    return discord.Embed(title=title, description=desc, color=0xE74C3C)

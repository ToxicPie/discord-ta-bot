import discord


def embed_color(title, desc, color=None, **kwargs):
    return discord.Embed(title=title, description=desc, color=color, **kwargs)

def embed_success(title=None, desc=None, **kwargs):
    return embed_color(title, desc, color=0x2ABF4A, **kwargs)

def embed_info(title=None, desc=None, **kwargs):
    return embed_color(title, desc, color=0x266FCF, **kwargs)

def embed_warning(title=None, desc=None, **kwargs):
    return embed_color(title, desc, color=0xFFBF00, **kwargs)

def embed_error(title=None, desc=None, **kwargs):
    return embed_color(title, desc, color=0xE74C3C, **kwargs)

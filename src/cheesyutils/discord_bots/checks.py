import discord
from discord.ext import commands
from .context import Context


def bot_owner_or_in_guild(*guilds: discord.Object):
    """A check that determines if a user is the bot owner or in a particular guild"""

    is_owner = commands.is_owner().predicate

    async def predicate(ctx: Context) -> bool:
        return (ctx.guild and ctx.guild.id in guilds) or await is_owner(ctx)

    return commands.check(predicate)


def is_guild_moderator():
    """A check that determines if a user is a guild moderator

    This is done by checking if the user has the following guild permissions:
    - `Manage Messages`
    - `Kick Members`
    - `Ban Members`
    """
    
    guild_only = commands.guild_only().predicate
    perms = commands.has_guild_permissions(manage_messages=True, kick_members=True, ban_members=True).predicate

    async def predicate(ctx: Context) -> bool:
        return await guild_only(ctx) and await perms(ctx)
    
    return commands.check(predicate)


def is_moderator():
    """A check that determins if a user is a moderator

    This is similar to `is_guild_moderator` except it uses `has_permissions` instead of `has_guild_permissions`
    """

    guild_only = commands.guild_only().predicate
    perms = commands.has_permissions(manage_messages=True, kick_members=True, ban_members=True).predicate

    async def predicate(ctx: Context) -> bool:
        return await guild_only(ctx) and await perms(ctx)
    
    return commands.check(predicate)


def bot_can_send_embeds():
    """A check that determines if the bot can send embeded messages in the current channel
    
    This is done by running `bot_has_permissions` for the following permissions:
    - `Send Messages`
    - `Embed Links`
    """

    perms = commands.has_permissions(send_messages=True, embed_links=True).predicate

    async def predicate(ctx: Context) -> bool:
        return await perms(ctx)
    
    return commands.check(predicate)


def bot_owner_or_permissions(**perms):
    """A check that determines if a user is the bot owner or if the author has specific permissions"""

    has_perms = commands.has_permissions(**perms).predicate
    is_owner = commands.is_owner().predicate

    async def predicate(ctx: Context) -> bool:
        return await has_perms(ctx) or await is_owner(ctx)
    
    return commands.check(predicate)


def bot_owner_or_guild_moderator():
    """A check that determines if a user is the bot owner or if the bot owner is a guild moderator"""

    is_mod = is_guild_moderator().predicate
    is_owner = commands.is_owner().predicate

    async def predicate(ctx: Context) -> bool:
        return await is_mod(ctx) or await is_owner(ctx)
    
    return commands.check(predicate)

import aiohttp
import asyncio
import datetime
import discord
import os
import re
from discord.ext import commands
from typing import Any, Awaitable, Callable, Optional, Union
from .help_command import HelpCommand
from .cogs.meta import Meta
from .context import Context
from .utils import *
from .database import *
from .embed import Embed


class DiscordBot(commands.Bot):
    """
    Defines a Discord Bot
    """

    def __init__(
            self,
            prefix: Optional[Union[str, Callable[[commands.Bot, discord.Message], str]]] = ".",
            color: Optional[Union[discord.Color, tuple, str]] = discord.Color.dark_theme(),
            database: Optional[str] = "bot.db",
            members_intent: Optional[bool] = False,
            presences_intent: Optional[bool] = False,
            status: Optional[str] = "online",
            activity: Optional[str] = None,
            loop: Optional[asyncio.BaseEventLoop] = None,
            custom_emojis: Optional[dict] = None,
            *args, **kwargs
    ):
        """Defines a new Discord Bot

        A lot of these attributes are optional and can be completely omitted if you so wish

        Attributes
        ----------
        prefix : Optional Union(str, Callable(commands.Bot, discord.Message)->str)
            The command prefix for the bot. This may also be a callable function (or coroutine) taking the bot as the first
            argument and the message context as the second argument, which returns the prefix string.
            This defaults to "."
        color : Optional Union(discord.Color, tuple, str)
            The default embed color to use for sending Discord embeds (defaults to `discord.Color.dark_theme()`)
            This parameter could be a `discord.Color` object, a hexadecimal color code, or an RGB tuple. The color will always
            end up being converted to a `discord.Color` object
        database : Optional str
            The name of the bot's sqlite database file (defaults to "bot.db")
        members_intent : Optional bool
            Whether to requests the `members` Discord API Intent (defaults to False).
            If this is set to true, you will need to ensure your bot has the
            `members` privileged intent enabled in the Discord Developer Portal
        presences_intent : Optional bool
            Whether to request the `presences` Discord API Intent (defaults to False)
            If this is set to true, you will need to ensure your bot has the
            `presences` privileged intent enabled in the Discord Developer Portal
        status : Optional str
            The online status to set for the bot (defaults to "online").
            This is case-insensitive and can be "online", "idle", "afk", "dnd", or "invisible"
        activity : Optional str
            The "playing" activity to set for the bot (defaults to "with Cheesy | (PREFIX)help)
        loop : Optional asyncio.BaseEventLoop
            The asyncio event loop to set for the bot (defaults to the value returned by `asyncio.get_event_loop()`)
        custom_emojis : Optional dict
            A dictionary who's string key corresponds to a particular Discord emoji string. Used for `Discord.Bot.get_emoji`
        """

        self.loop = loop or asyncio.get_event_loop()
        self.color = get_discord_color(color)

        # set intents
        intents: discord.Intents = discord.Intents.default()
        intents.members = members_intent
        intents.presences = presences_intent

        # set activity
        if activity is None:
            activity = f"with Cheesy | {prefix}help"

        # set database
        self.database = Database(database)

        self.start_time = None

        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            intents=intents,
            activity=discord.Game(name=activity),
            status=self.get_discord_status(status),
            help_command=HelpCommand(self.color),
            *args, **kwargs
        )

        self.custom_emojis = custom_emojis

        self.add_cog(Meta(self))

    async def on_ready(self):
        if not self.start_time:
            self.start_time = datetime.datetime.utcnow()
            print(f"{self.user} is ready!")
    
    def run(self, token: Union[os.PathLike, str]):
        """Starts the bot

        Starting the bot can be done by the following methods:
        - Providing the raw token
        - Providing the path to a text file containing the token.
        This is done by reading the first line of the file and stripping trailing spaces

        Parameters
        ----------
        token : Union(os.PathLike, str)
            The token or the path to a text file containing the token
        """

        try:
            with open(token, "r") as file:
                token = file.readlines()[0].strip()
        except (FileNotFoundError, PermissionError, FileExistsError) as e:
            print(f"Assuming raw token passed - could not find token file due to an error: \"{e.__class__.__name__}\"")
            token = token

        try:
            super().run(token)
        except (aiohttp.ClientConnectorError, discord.HTTPException, discord.LoginFailure) as e:
            print(f"Unable to start bot: \"{type(e)}\" - \"{e}\"")

    def get_emoji(self, id: Union[str, int]) -> Optional[discord.Emoji]:
        """Returns a Discord Emoji

        This method slightly differs from discord.py's implementation.
        For starters, the bot will first look inside it's user-defined emoji reference (see `DiscordBot.custom_emojis`).
        From there, the bot will continue to search for the emoji in it's cache similar to discord.py's implementation

        Parameters
        ----------
        id : Union(str, int)
            The Discord ID OR a key for `DiscordBot.custom_emojis`
        
        Returns
        -------
        Optional discord.Emoji
        """

        if isinstance(id, str):
            # lookup key in the bot's custom emoji key
            if self.custom_emojis is not None:
                emoji_str = self.custom_emojis.get(id)
                
                if emoji_str is not None:
                    def extract_emoji_id(emoji: str) -> int:
                        return int(re.match(r'<a?:[a-zA-Z0-9\_]+:([0-9]+)>$', emoji).group(1))

                    return super().get_emoji(extract_emoji_id(emoji_str))

        # defaults to parent method should the above fail
        return super().get_emoji(id)

    async def paginate(
        self,
        ctx: commands.Context,
        embed_title: str,
        line: str,
        sequence: list,
        prefix: Optional[str] = "",
        suffix: Optional[str] = "",
        max_page_size: Optional[int] = 2048,
        other_sequence: Optional[list] = None,
        sequence_type_name: Optional[str] = None,
        author_name: Optional[str] = None,
        author_icon_url: Optional[str] = None,
        count_format: Optional[str] = None
    ):
        """Creates a paginating menu given a particular context

        Warning: The following permissions are required for the bot to utilize pagination
        - Add Reactions
        - Manage Messages

        Parameters
        ----------
        ctx : commands.Context
            The context in which the pagination is to take place
        embed_title : str
            The title to use for the embed
        line : str
            The format string to use for each line in a page. Each item in `sequence` gets its own line in a page
        sequence : list
            The sequence in which pagination should take place
        embed_color : Optional discord.Color
            The embed color to use. Defaults to `discord.Color.dark_theme()`
        prefix : Optional str
            The string to prepend to the beginning of the page (defaults to an empty string)
        suffix : Optional str
            The string to append to the end of the page (defaults to an empty string)
        max_page_size : Optional int
            The maximum number of characters per page (defaults to 2048)
        other_sequence : Optional list
            The other sequence to iterate over (mainly for the embed's footer text, defaults to be equal to `sequence`)
        sequence_type_name : Optional str
            The name of the other sequence (mainly for the embed's footer text, defaults to "items")
        author_name : Optional str
            The name to use for the embed author (defaults to the current guild's name)
        author_icon_url : Optional str
            The icon url to use for the embed author (defaults to the current guild's icon)
        count_format : Optional str
            The string to prepend to each line (used for a count)
        """

        await paginate(
            ctx, embed_title, line, sequence, self.color,
            prefix, suffix, max_page_size, other_sequence,
            sequence_type_name, author_name, author_icon_url, count_format
        )
    
    @staticmethod
    def get_discord_status(status: str) -> discord.Status:
        """Returns a discord status from a string

        This is mainly used for bot initiation

        The provided string is automatically converted to lowercase, providing the following valid options:
        - "online" (Online)
        - "away" (Idle)
        - "idle" (Idle)
        - "dnd" (Do not Disturb)
        - "do not disturb" (Do not Disturb)

        Parameters
        ----------
        status : str
            The string to convert into a discord.Status
        
        Raises
        ------
        ValueError if the provided string could not be converted to a discord.Status

        Returns
        -------
        A discord.Status representation of the given string
        """

        status_lower = status.lower()

        if status_lower == "dnd" or status_lower == "do not disturb":
            return discord.Status.dnd
        elif status_lower == "idle" or status_lower == "away":
            return discord.Status.idle
        elif status_lower == "online":
            return discord.Status.online
        else:
            raise ValueError(f"Invalid status string \"{status}\"")
        
    async def _send_emoji_prepended_embed(self, ctx: discord.abc.Messageable, emoji: str, content: str, color: discord.Color):
        """Sends an embed with an emoji and space both prepended to the left of the desired content to send

        This is mostly here to avoid dupicate code

        Parameters
        ----------
        ctx : discord.abc.Messageable
            The channel, context, or user to send the embed to
        emoji : str
            The desired emoji to prepend to `content`
        content : str
            The content to send. `emoji` and a space automatically prepended
            and truncated into the embed description
        color : discord.Color
            The color to make the embed
        """

        embed = Embed(description=f"{emoji} {content}", color=color, timestamp=discord.Embed.Empty)
        await ctx.send(embed=embed)

    async def send_success_embed(self, ctx: discord.abc.Messageable, content: str):
        """Sends an embed with a white checkmark emoji and a space prepended to the rest of the content

        The description is automatically truncated to the maximum allowed embed description length

        Parameters
        ----------
        ctx : discord.abc.Messageable
            The channel, context, or user to send the embed to
        content : str
            The content to send. There is a ":white_check_mark:" emoji and a space automatically prepended
            and truncated into the embed description
        """

        await self._send_emoji_prepended_embed(ctx, ":white_check_mark:", content, discord.Color.green())

    async def send_fail_embed(self, ctx: discord.abc.Messageable, content: str):
        """Sends an embed with a x emoji and a space prepended to the rest of the content

        The description is automatically truncated to the maximum allowed embed description length

        Parameters
        ----------
        ctx : discord.abc.Messageable
            The channel, context, or user to send the embed to
        content : str
            The content to send. There is a ":x:" emoji and a space automatically prepended
            and truncated into the embed description
        """

        await self._send_emoji_prepended_embed(ctx, ":x:", content, discord.Color.red())
    
    async def send_warn_embed(self, ctx: discord.abc.Messageable, content: str):
        """Sends an embed with a warning emoji and a space prepended to the rest of the content

        The description is automatically truncated to the maximum allowed embed description length

        Parameters
        ----------
        ctx : discord.abc.Messageable
            The channel, context, or user to send the embed to
        content : str
            The content to send. There is a ":warning:" emoji and a space automatically prepended
            and truncated into the embed description
        """

        await self._send_emoji_prepended_embed(ctx, ":warning:", content, discord.Color.gold())

    @staticmethod
    async def _retrieve_entity(snowflake: int, func: Callable[[int], Any], coro: Awaitable[int]):
        """Lazily retrieves a discord object from a given discord id
        
        This function is moreso designed to be a helper function for other `retrieve_X` coroutines,
        which can be found below, in order to lazily fetch discord objects in order to reduce API calls

        Parameters
        ----------
        snowflake : int
            The discord id of the object to retrieve
        func : Callable(int)
            The function to initially call before attempting to fetch using `coro` if needed
        coro : Awaitable(int)
            The coroutine to await should the result of `func` be equal to None
        
        Returns
        -------
        The respective Discord object, or None if the object was unable to be retrieved
        """

        entity = func(snowflake)
        if entity is None:
            try:
                return await coro(snowflake)
            except (discord.HTTPException, discord.InvalidData):
                return None
        else:
            return entity

    async def retrieve_channel(
            self,
            channel_id: int
    ) -> Optional[Union[discord.abc.GuildChannel, discord.abc.PrivateChannel]]:
        """Lazily retrieves a Discord channel

        NOTE: Per discord.py's documentation, you can only retrieve channels
        that the bot currently has access to. This means that a given channel id
        could be valid, but if the bot doesn't have access to it, the bot will not
        be able to retrieve it. In that case, this function will return None

        Parameters
        ----------
        channel_id : int
            The Discord ID of the channel you wish to retrieve

        Returns
        -------
        An discord.abc.GuildChannel for guild-specific channels,
        or discord.abc.PrivateChannel for user specific channels (DMs),
        or None if the channel could not be retrieved
        """

        return await self._retrieve_entity(channel_id, self.get_channel, self.fetch_channel)

    async def retrieve_guild(self, guild_id: int) -> Optional[discord.Guild]:
        """Lazily retrieves a Discord guild

        NOTE: Per discord.py's documentation, you can only retrieve guilds
        that the bot currently has access to. This means that a given guild id
        could be valid, but if the bot doesn't have access to it, the bot will not
        be able to retrieve it. In that case, this function will return None

        Parameters
        ----------
        guild_id : int
            The Discord ID of the guild you wish to retrieve
        
        Returns
        -------
        A discord.Guild if the guild could be retrieved, or None of the guild
        was not found or if the bot does not have access to the respective guild
        """

        return await self._retrieve_entity(guild_id, self.get_guild, self.fetch_guild)

    async def retrieve_user(self, user_id: int) -> Optional[discord.User]:
        """Lazily retrieves a Discord User

        Parameters
        ----------
        user_id : int
            The Discord ID of the user you wish to retrieve
        
        Returns
        -------
        A discord.User if the user could be retrieved, None otherwise
        """

        return await self._retrieve_entity(user_id, self.get_user, self.fetch_user)

    async def retrieve_message(
            self,
            channel_id: Optional[int] = None,
            message_id: Optional[int] = None,
            message_link: Optional[str] = None
    ) -> Optional[discord.Message]:
        """Lazily retrieves a Discord Message

        There are two ways to retrieve messages via this method
        - By supplying the `channel_id` and `message_id` parameters with their respective values
        - By supplying the `message_link`
        - Supplying both of the above will retrieve from `message_id` and `channel_id` only
        
        NOTE: Per discord.py's documentation, you can only retrieve messages
        that the bot currently has access to. This means that a given message/channel id
        or message link could be valid, but if the bot doesn't have access to where the
        message is located, the bot will not be able to retrieve it. In that case, this
        function will return None

        Parameters
        ----------
        channel_id : Optional int
            The Discord ID of the channel where the message you wish to retrieve is located
        message_id : Optional int
            The Discord ID of the message you wish to retrieve
        message_link : Optional str
            The url of the message link for the message you wish to retrieve
            Note that if this parameter is supplied, this method is called again
            using the channel/message id extracted from the url

        Returns
        -------
        A discord.Message if the message could be retrieved, None otherwise
        """

        if channel_id is not None and message_id is not None:
            channel = await self.retrieve_channel(channel_id)
            if channel is not None:
                try:
                    return await channel.fetch_message(message_id)
                except discord.HTTPException:
                    return None
            else:
                return None
        elif message_link is not None:
            try:
                channel_id, message_id = message_link.split("/")[5:]
                return await self.retrieve_message(int(channel_id), int(message_id))
            except (IndexError, ValueError):
                return None
        else:
            return None

    async def retrieve_member(
            self,
            guild: Union[discord.Guild, int],
            user_id: int
    ) -> Optional[discord.Member]:
        """Lazily retrieves a Discord guild member

        NOTE: Per discord.py's documentation, you can only retrieve members from guilds
        that the bot currently has access to. This means that a given user/guild id
        could be valid, but if the bot doesn't have access to the guild, the bot will not
        be able to retrieve the member. In that case, this function will return None
        
        Parameters
        ----------
        guild : Union(discord.Guild, int)
            The guild id of the guild or the guild object itself to retrieve the desired member from.
            Note that if a guild id is supplied rather than a guild object, the guild will have to be
            retrieved
        user_id : int
            The Discord ID of the member you wish to retrieve

        Returns
        -------
        A discord.Member if the member could be retrieved, None otherwise
        """

        if isinstance(guild, discord.Guild):
            guild = guild
        elif isinstance(guild, int):
            guild = await self.retrieve_guild(guild)
            if guild is None:
                return None
        else:
            raise ValueError(f"Invalid Guild type. Must be discord.Guild or int, not \"{type(guild)}\"")

        member = guild.get_member(user_id)
        if member is None:
            try:
                return await guild.fetch_member(user_id)
            except discord.HTTPException:
                return None
        else:
            return member
    
    async def get_context(self, message: discord.Message, cls=Context):
        return await super().get_context(message, cls=cls)

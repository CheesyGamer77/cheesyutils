import cheesyutils
import copy
import datetime
from inspect import Parameter
import discord
import re
from contextlib import redirect_stdout
from discord.ext import commands
from io import StringIO
from textwrap import indent
from traceback import format_exc
from typing import Callable, List, Optional, Union
from ..utils import get_base_embed, paginate


class _ConversionFailed(commands.BadArgument):
    """Raised when a conversion on a particular argument fails

    This inherits from `discord.ext.commands.BadArgument`
    
    Attributes
    ----------
    argument : str
        The argument that failed to be converted
    """

    def __init__(self, argument: str, *args, **kwargs):
        self.argument = argument
        super().__init__(*args, **kwargs)


class _CogConverter(commands.Converter):
    """Converter to convert strings into cogs"""

    async def convert(self, ctx: commands.Context, argument: str) -> commands.Cog:
        """Attempts to convert a string into a named cog OR the cog's file extension

        Parameters
        ----------
        ctx : commands.Context
            The invokation context, usually fed from an executing command
        argument : str
            The argument to attempt to convert into a named cog
        
        Raises
        ------
        `_ConversionFailed` if the cog was not found
        """

        cog = ctx.bot.get_cog(argument)
        if cog is None:
            raise _ConversionFailed(argument, f"No cog named {argument!r} found")
        return cog


class _ExtensionConverter(commands.Converter):
    """Converter to convert strings into extensions"""
    
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            return ctx.bot.extensions[argument]
        except KeyError:
            raise _ConversionFailed(argument, f"No extension named {argument!r} found")


class _ValidPrefix(commands.Converter):
    """Converter for converting strings into valid prefixes"""

    async def convert(self, ctx: commands.Context, argument: str):
        """Attempts to convert a given argument into a valid prefix

        A valid prefix is a sequence of alphanumeric and special characters

        Parameters
        ----------
        ctx : commands.Context
            The invokation context, usually fed from an executing command
        argument : str
            The argument to attempt to convert into a valid prefix

        Raises
        ------
        `_ConversionFailed` if the prefix was invalid
        """

        if not re.match(r"^\S{1,4}$"):
            raise _ConversionFailed(argument, f"{argument!r} is not a valid prefix")
        return argument


class _AnyChannel(commands.Converter):
    """Converter for converting channel mentions, Discord IDs, etc into a valid Discord channel

    Taken from the `GlobalChannel` converter from https://github.com/Rapptz/RoboDanny/blob/644e588851bccca24f220b74f0ef091c48299757/cogs/admin.py
    """

    async def convert(self, ctx: commands.Context, argument: str):
        """Attempts to convert any Discord ID to a valid Discord Text Channel, Voice Channel, etc that the bot can fetch/see

        Parameters
        ----------
        ctx : commands.Context
            The invokation context, usually fed from an executing command
        argument : str
            The argument to attempt to convert into a Discord channel
        
        Raises
        ------
        `_ConversionFailed` if the channel was not found
        """

        try:
            return await commands.TextChannelConverter().convert(argument)
        except commands.BadArgument:
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                # couldn't convert argument to channel id
                raise _ConversionFailed(argument, "Couldn't convert {argument!r} into a global channel to fetch")
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is not None:
                    raise _ConversionFailed(argument, f"No channel with ID {argument!r} found")


class _NoCustomPrefixesAllowed(commands.CheckFailure):
    """Raised when a bot is not able to utilize custom prefix commands

    Inherits from `discord.ext.commands.CheckFailure`
    """

    pass


def _can_use_custom_prefixes():
    """A decorator used internally to determine whether a bot is able to use custom prefixes or not

    The decorator does this by checking if a sqlite table with the name of `prefixes` exists within the bot's database
    """

    async def predicate(ctx: commands.Context):
        tables = await ctx.bot.database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prefixes'")
        return len(tables) != 0
    
    try:
        return commands.check(predicate)
    except commands.CheckFailure:
        raise _NoCustomPrefixesAllowed


class Meta(commands.Cog):
    """
    Default commands and listeners and stuffs
    """

    def __init__(self, bot):
        self.bot = bot
    
    @staticmethod
    def _cleanup_code(content: str) -> str:
        """Automatically removes code blocks from the code.

        This is just used for the `execute` command at this time
        
        Parameters
        ----------
        content : str
            The content to remove code blocks from
        
        Returns
        -------
        The cleaned content as a string
        """

        # remove \`\`\`py\n\`\`\`
        if content.startswith('```') and content.endswith('```'):
            if content[-4] == '\n':
                return '\n'.join(content.split('\n')[1:-1])
            return '\n'.join(content.split('\n')[1:]).rstrip('`')

        # remove `foo`
        return content.strip('` \n')

    async def _on_prefix_commands_error(self, ctx: commands.Context, error):
        if isinstance(error, _NoCustomPrefixesAllowed):
            await self.bot.send_fail_embed(ctx, "This bot is not able to utilize custom prefixes")
        elif isinstance(error, _ConversionFailed):
            await self.bot.send_fail_embed(ctx, f"{error.argument!r} is not a valid prefix")

    @commands.guild_only()
    @_can_use_custom_prefixes()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.group(name="prefix")
    async def prefix_group(self, ctx: commands.Context):
        """
        Commands for getting/modifying the bot's prefix for the current guild

        You can run this command on it's own in order to return the guild's current prefix. This is equivalent to the `prefix get` command
        """
        
        pass

    @prefix_group.error
    async def on_prefix_group_error(self, ctx: commands.Context, error):
        await self._on_prefix_commands_error(ctx, error)

    @commands.guild_only()
    @_can_use_custom_prefixes()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @prefix_group.command(name="get")
    async def get_prefix_command(self, ctx: commands.Context):
        """
        Returns the bot's prefix for the current guild

        This is equivalent to just running the `prefix` command on its own
        """

        prefix = self.bot.database.execute("SELECT prefix FROM prefixes WHERE server_id = ?", parameters=(ctx.guild.id,))
        
        embed = get_base_embed(title="Bot Prefix", author=ctx.guild)
        embed.add_field(
            name="Prefix",
            value=prefix
        )

        await ctx.send(embed=embed)

    @get_prefix_command.error
    async def on_get_prefix_command_error(self, ctx: commands.Context, error):
        await self._on_prefix_commands_error(ctx, error)

    @commands.guild_only()
    @_can_use_custom_prefixes()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @prefix_group.command(name="set")
    async def set_prefix_command(self, ctx: commands.Context, prefix: _ValidPrefix):
        """
        Sets the bot's prefix for the current guild

        The prefix must be a sequence containing up to four alphanumeric characters or special characters
        """

        await self.bot.database.execute("INSERT OR REPLACE INTO prefixes(server_id, prefix) VALUES (?, ?)", parameters=(ctx.guild.id, prefix))
        await self.bot.send_success_embed(ctx, f"Prefix set to {prefix!r}")

    @set_prefix_command.error
    async def on_set_prefix_command_error(self, ctx: commands.Context, error):
        await self._on_prefix_commands_error(ctx, error)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @prefix_group.command(name="reset")
    async def reset_prefix_command(self, ctx: commands.Context):
        """
        Resets the bot's prefix for the current guild
        """

        old_prefix = await self.bot.get_prefix(ctx.message)

        # this is a really dumb way to reset a sqlite column to its default value
        await self.bot.database.execute("DELETE FROM prefixes WHERE server_id = ?", parameters=(ctx.guild.id,))
        await self.bot.database.execute("INSERT INTO prefixes(server_id) VALUES (?)", parameters=(ctx.guild.id,))

        new_prefix = await self.bot.get_prefix(ctx.message)

        await self.bot.send_success_embed(ctx, f"Prefix reset from {old_prefix!r} to {new_prefix!r}")

    @reset_prefix_command.error
    async def on_reset_prefix_command_error(self, ctx: commands.Context, error):
        await self._on_prefix_commands_error(ctx, error)

    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @commands.command()
    async def execute(self, ctx: commands.Context, *, content: str):
        """
        Evaluates some python code
        Gracefully stolen from Rapptz ->
        https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L72-L117
        """

        # make the environment
        # this allows you to reference particular
        # variables in your block of code in discord
        # if you want to get technical, this is an
        # implementation of a Symbol Table
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'self': self
        }
        env.update(globals())

        # make code and output string
        content = self._cleanup_code(content)
        stdout = StringIO()
        to_compile = f'async def func():\n{indent(content, "  ")}'

        # create the function to be ran
        try:
            exec(to_compile, env)
        except Exception as e:
            # compilation error
            # send the error in a code block
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        # execute the function we just made
        func = env["func"]
        try:
            # force stdout into StringIO
            with redirect_stdout(stdout):
                # run our function
                ret = await func()
        except Exception:
            # runtime error
            # output the error in a code block
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{format_exc()}\n```')
        else:
            # hey we didn't goof up

            # react with a white check mark to show that it ran
            try:
                await ctx.message.add_reaction("\u2705")
            except Exception:
                pass

            # if nothing was returned, it might have printed something
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                text = f'```py\n{value}{ret}\n```'

                # character limits are a thing
                if len(text) > 2000:
                    # over max limit
                    # send output in a file
                    return await ctx.send(
                        file=discord.File(
                            StringIO('\n'.join(text.split('\n')[1:-1])),
                            filename='ev.txt'
                        )
                    )
                await ctx.send(text)

    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.command(name="stats")
    async def stats_command(self, ctx: commands.Context):
        """
        Display's bot information
        """

        embed = get_base_embed(
            title="Bot Stats",
            author=self.bot
        )

        embed.add_field(
            name=f"Libraries",
            value=f"<:discord_py:840064300923879434> [discord.py](https://github.com/Rapptz/discord.py) - `{discord.__version__}`\n"
                  f"<:cheese_think:787739437715030066> [cheesyutils](https://github.com/CheesyGamer77/cheesyutils) - `{cheesyutils.__version__}`",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="sudo")
    async def sudo_command(self, ctx: commands.Context, channel: Optional[_AnyChannel], user: Union[discord.Member, discord.User], *, command: str):
        """
        Executes a command as another user, in another channel

        The `channel` parameter is optional and defaults to the current channel if not supplied, and does not have to be a channel from the current guild
        """

        message = copy.copy(ctx.message)
        channel = channel or ctx.channel
        
        # reconstruct message so that it points in the other channel
        message.channel = channel
        message.author = user
        message.content = ctx.prefix + command
        context = await self.bot.get_context(message, cls=type(ctx))
        await self.bot.invoke(context)

    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @commands.group(name="cog")
    async def _cog_group(self, ctx: commands.Context):
        """
        Cog related commands and utilities
        """

        pass

    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @_cog_group.command(name="list")
    async def _cog_list_command(self, ctx: commands.Context, cogs_or_extensions: Optional[str]="cogs"):
        """
        Lists all cogs currently running on the bot
        """

        if cogs_or_extensions == "cogs":
            sequence = self.bot.cogs.keys()
        elif cogs_or_extensions == "extensions":
            sequence = self.bot.extensions.keys()
        else:
            raise _ConversionFailed(cogs_or_extensions, f"{cogs_or_extensions!r} is not a valid mode")

        # TODO - still uses old pagination
        await paginate(
            ctx,
            embed_title="Cog List",
            line="`{0}`",
            sequence=sequence,
            max_page_size=1024,
            sequence_type_name="cogs",
            author_name=str(self.bot.user),
            author_icon_url=self.bot.user.avatar_url
        )

    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @_cog_group.command(name="info")
    async def _cog_info_command(self, ctx: commands.Context, cog: _CogConverter):
        """
        Returns info about a given cog
        """

        embed = get_base_embed(
            title=f"Cog Info - {cog.qualified_name}",
            description=cog.description if cog.description != "" else "(No Description Provided)",
            color=self.bot.color,
            author=ctx.bot.user
        )

        listeners = cog.get_listeners()
        fmt = ', '.join(sorted([f'`{listener[0]}`' for listener in listeners])) if len(listeners) != 0 else "None"

        embed.add_field(
            name=f"Event Listeners[{len(listeners)}]",
            value=fmt,
            inline=False
        )

        commands = cog.get_commands()
        fmt = ', '.join(sorted([f'`{cmd.name}`' for cmd in commands])) if len(commands) != 0 else "None"
        embed.add_field(
            name=f"Commands[{len(commands)}]",
            value=fmt
        )

        await ctx.send(embed=embed)
    
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @_cog_group.command(name="load")
    async def _cog_load_command(self, ctx: commands.Context, cog: str):
        """
        Loads a particular cog
        """

        if await self._execute_extension_actions(ctx, cog, self.bot.load_extension):
            await self.bot.send_success_embed(ctx, f"Cog `{cog}` was loaded!")
    
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @_cog_group.command(name="unload")
    async def _cog_unload_command(self, ctx: commands.Context, cog: str):
        """
        Unloads a particular cog
        """

        if await self._execute_extension_actions(ctx, cog, self.bot.unload_extension):
            await self.bot.send_success_embed(ctx, f"Cog `{cog}` was unloaded!")
    
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @_cog_group.command(name="reload")
    async def _cog_reload_command(self, ctx: commands.Context, cog: str):
        if await self._execute_extension_actions(ctx, cog, self.bot.unload_extension, self.bot.load_extension):
            await self.bot.send_success_embed(ctx, f"Cog `{cog}` was reloaded!")

    async def _execute_extension_actions(self, ctx: commands.Context, cog: str, *funcs: List[Callable[[str], None]]):
        """Executes a list of extension actions

        This is used as a method of abstracting extension error handling away from the cog commands

        Parameters
        ----------
        ctx : discord.commands.Context
            The invocation context
        cog : str
            The name of the cog to execute the actions on
        funcs : List of Callable(str)->None
            A list of callables, which take in the cog's name, to execute
        """

        try:
            for func in funcs:
                func(cog)
            return True
        except commands.ExtensionNotFound as e:
            await self.bot.send_fail_embed(ctx, f"Cog `{e.name}` was not found")
        except commands.ExtensionAlreadyLoaded as e:
            await self.bot.send_fail_embed(ctx, f"Cog `{e.name}` is already loaded")
        except commands.ExtensionNotLoaded as e:
            await self.bot.send_fail_embed(ctx, f"Cog `{e.name}` is already unloaded")
        except commands.NoEntryPointError as e:
            await self.bot.send_fail_embed(ctx, f"Cog `{e.name}` is missing `setup` entrypoint")
        except commands.ExtensionFailed as e:
            await self.bot.send_fail_embed(ctx, f"Cog `{e.name}` initiation failed: `{e.original.__class__.__name__}`")

    @_cog_list_command.error
    async def on_cog_list_command_error(self, ctx: commands.Context, error):
        if isinstance(error, _ConversionFailed):
            await self.bot.send_fail_embed(ctx, f"Invalid list mode {error.argument!r}")

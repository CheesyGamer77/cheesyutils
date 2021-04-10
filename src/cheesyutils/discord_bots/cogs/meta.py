import datetime
import discord
from contextlib import redirect_stdout
from discord.ext import commands
from io import StringIO
from textwrap import indent
from traceback import format_exc


class CogConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> commands.Cog:
        cog = ctx.bot.get_cog(argument)
        if cog is None:
            raise commands.ExtensionNotFound(argument)
        return cog


class Meta(commands.Cog):
    """
    Default commands and listeners and stuffs
    """

    def __init__(self, bot):
        self.bot = bot
    
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
                        file=discord.File(StringIO('\n'.join(text.split('\n')[1:-1])),
                                          filename='ev.txt')
                    )
                await ctx.send(text)
    
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
    @_cog_group.command(name="info")
    async def _cog_info_command(self, ctx: commands.Context, cog: CogConverter):
        """
        Returns info about a given cog
        """

        embed = discord.Embed(
            title=f"Cog Info - {cog.qualified_name}",
            description=cog.description if cog.description != "" else "(No Description Provided)",
            color=self.bot.color,
            timestamp=datetime.datetime.utcnow()
        )

        embed.set_author(
            name=str(ctx.bot.user),
            icon_url=ctx.bot.user.avatar_url
        )

        listeners = cog.get_listeners()
        fmt = ', '.join(sorted([f'`{listener[0]}`' for listener in listeners])) if len(listeners) != 0 else "None"

        embed.add_field(
            name=f"Listeners[{len(listeners)}]",
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
    @commands.bot_has_permissions(send_messages=True)
    @_cog_group.command(name="load")
    async def _cog_load_command(self, ctx: commands.Context, cog: str):
        """
        Loads a particular cog
        """

        self.bot.load_extension(cog)
        await self.bot.send_success_embed(ctx, f"Cog `{cog}` was loaded!")
    
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @_cog_group.command(name="unload")
    async def _cog_unload_command(self, ctx: commands.Context, cog: str):
        """
        Unloads a particular cog
        """

        self.bot.unload_extension(cog)
        await self.bot.send_success_embed(ctx, f"Cog `{cog}` was unloaded!")
    
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    @_cog_group.command(name="reload")
    async def _cog_reload_command(self, ctx: commands.Context, cog: str):
        self.bot.unload_extension(cog)
        self.bot.load_extension(cog)
        await self.bot.send_success_embed(ctx, f"Cog `{cog}` was reloaded!")

    @_cog_info_command.error
    async def on_cog_commands_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.ExtensionNotFound):
            await self.bot.send_fail_embed(ctx, f"Cog `{error.name}` was not found")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await self.bot.send_fail_embed(ctx, f"Cog `{error.name}` is already loaded")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await self.bot.send_fail_embed(ctx, f"Cog `{error.name}` is already unloaded")
        elif isinstance(error, commands.NoEntryPointError):
            await self.bot.send_fail_embed(ctx, f"Cog `{error.name}` is missing `setup` entrypoint")
        elif isinstance(error, commands.ExtensionFailed):
            await self.bot.send_fail_embed(ctx, f"Cog {error.name} initiation failed: `{error.original.__class__.__name__}`")
        
        print(error, error.__class__.__name__)

    @_cog_load_command.error
    async def on_cog_load_command_error(self, ctx: commands.Context, error):
        await self.on_cog_commands_error(ctx, error)
    
    @_cog_unload_command.error
    async def on_cog_unload_command_error(self, ctx: commands.Context, error):
        await self.on_cog_commands_error(ctx, error)

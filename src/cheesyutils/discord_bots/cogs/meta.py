import discord
from contextlib import redirect_stdout
from discord.ext import commands
from io import StringIO
from textwrap import indent
from traceback import format_exc


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

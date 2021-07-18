import asyncio
import discord
from discord.ext import commands
from typing import Optional, Union
from .embed import Embed


class Context(commands.Context):
    async def show_help(self, command: commands.Command=None):
        """Invokes the help command for a particular command

        This differs from the builtin `context.send_help` as this command
        defaults to the current command being executed if `command` is `None`

        Parameters
        ----------
        command : commands.Command
            The command to show help for.
            This defaults to `None`
        """
        
        if not command:
            cmd = self.bot.get_command("help")
            command = command or self.command.qualified_name
            await self.invoke(cmd, command=command)
    
    def get_success_embed(self, content: str) -> Embed:
        return Embed(
            description=f":white_check_mark: {content}",
            color=discord.Color.green()
        )
    
    def get_warning_embed(self, content: str) -> Embed:
        return Embed(
            description=f":warning: {content}",
            color=discord.Color.gold()
        )
    
    def get_fail_embed(self, content: str) -> Embed:
        return Embed(
            description=f":x: {content}",
            color=discord.Color.red()
        )

    async def send_success(self, content: str):
        """Sends an embed communicating successful completion

        Parameters
        ----------
        content : str
            The message to set as the success embed's description
        """

        await self.send(embed=self.get_success_embed(content))
    
    async def send_warning(self, content: str):
        """Sends an embed communicating a warning

        Parameters
        ----------
        content : str
            The message to set as the warning embed's description
        """

        await self.send(embed=self.get_warning_embed(content))

    async def send_fail(self, content: str):
        """Sends an embed communicating that a failure has occured

        Parameters
        ----------
        content : str
            The message to set as the fail embed's description
        """
        
        await self.send(embed=self.get_fail_embed(content))

    async def reply_success(self, content: str, mention_author: bool = True):
        """Replies to the original message with an embed communicating successful completion

        Parameters
        ----------
        content : str
            The message to set as the success embed's description
        mention_author : bool
            Whether to mention the context message's author in the reply.
            This defaults to `True`.
        """

        await self.reply(embed=self.get_success_embed(content), mention_author=mention_author)
    
    async def reply_warning(self, content: str, mention_author: bool = True):
        """Replies to the original message with an embed communicating a warning

        Parameters
        ----------
        content : str
            The message to set as the warning embed's description
        mention_author : bool
            Whether to mention the context message's author in the reply.
            This defaults to `True`.
        """

        await self.reply(embed=self.get_warning_embed(content), mention_author=mention_author)
    
    async def reply_fail(self, content: str, mention_author: bool = True):
        """Replies to the original message with an embed communicating that a failure has occured

        Parameters
        ----------
        content : str
            The message to set as the fail embed's description
        mention_author : bool
            Whether to mention the context message's author in the reply.
            This defaults to `True`.
        """

        await self.reply(embed=self.get_fail_embed(content), mention_author=mention_author)

    async def prompt(self, base_embed: Embed, *, timeout: float=60.0, delete_after: bool=False, user: Union[discord.Member, discord.User]=None) -> Optional[bool]:
        """Starts an interactive confirmation prompt via reactions

        This will eventually be refactored to use message components instead

        Parameters
        ----------
        base_embed : Embed
            The embed to send as the prompt
        timeout : float
            The ammount of seconds before the prompt times out.
            This defaults to `60.0`
        delete_after : bool
            Whether to delete the prompt message after a reaction has been made.
            This defaults to `False`
        user : Union[discord.Member, discord.User]
            The user to prompt. Only reactions from this user will be accepted.
            This default's to the author of the context's message
        
        Returns
        -------
        `True` if the user approved, `False` if the user denied`, or `None` if the prompt timed out
        """

        message: discord.Message = await self.send(embed=base_embed)

        lookup = {
            "\U00002705": True,
            "\U000026D4": False
        }

        for emoji in lookup.keys():
            await message.add_reaction(emoji)


        user_id = user.id or self.author.id

        def check(payload: discord.RawReactionActionEvent) -> bool:
            if payload.message_id == message.id and payload.user_id == user_id:
                return str(payload.emoji) in lookup.keys()
            return False
        
        confirm = None

        try:
            payload: discord.RawReactionActionEvent = await self.bot.wait_for("raw_reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            return confirm

        confirm = lookup[str(payload.emoji)]

        try:
            if delete_after:
                await message.delete()
        finally:
            return confirm

        

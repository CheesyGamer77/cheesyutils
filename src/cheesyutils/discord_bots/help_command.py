import discord
from discord.ext import commands
from typing import List, Mapping, Optional
from .utils import get_base_embed


class HelpCommand(commands.HelpCommand):
    def __init__(self, color: discord.Color):
        self.color = color
        super().__init__()

    def get_command_signature(self, command: commands.Command):
        return f"`{self.clean_prefix}{command.qualified_name} {command.signature}`".strip()

    async def get_bot_help_embed(self, ctx: commands.Context, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]) -> discord.Embed:
        embed = get_base_embed(
            title="Help",
            color=self.color,
            author=ctx.me,
            footer_icon=ctx.me,
            footer_text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group"
        )

        for cog, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        return embed

    def get_command_help_embed(self, ctx: commands.Context, command: commands.Command) -> discord.Embed:
        embed = get_base_embed(
            title=f"Command Help: {command.name}",
            description=command.help if command.help is not None else "None",
            color=self.color,
            author=ctx.me,
            footer_icon=ctx.me,
            footer_text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group"
        )

        if len(command.aliases) > 0:
            embed.add_field(
                name="Aliases",
                value=", ".join([f"`{alias}`" for alias in command.aliases]),
                inline=False
            )

        embed.add_field(
            name="Signature",
            value=self.get_command_signature(command),
            inline=False
        )

        if command.usage is not None:
            embed.add_field(
                name="Usage",
                value=command.usage,
                inline=False
            )
        
        return embed

    def get_group_help_embed(self, ctx: commands.Context, group: commands.Group):
        embed = get_base_embed(
            title=f"Group Help: {group.name}",
            description=group.help,
            color=self.color,
            author=ctx.me,
            footer_icon=ctx.me,
            footer_text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group"
        )

        if len(group.aliases) > 0:
            embed.add_field(
                name="Aliases",
                value=", ".join([f"`{alias}`" for alias in group.aliases]),
                inline=False
            )

        if group.cog_name is not None:
            embed.add_field(
                name="Cog",
                value=group.cog_name,
                inline=False
            )

        if group.signature != "":
            embed.add_field(
                name="Signature",
                value=group.signature,
                inline=False
            )

        if group.usage is not None:
            embed.add_field(
                name="Usage",
                value=group.usage,
                inline=False
            )

        if len(group.commands) > 0:
            embed.add_field(
                name="Commands",
                value=", ".join(sorted([f"`{command.name}`" for command in group.commands], key=lambda s: s)),
                inline=False
            )
        
        return embed

    def get_cog_help_embed(self, ctx: commands.Context, cog: commands.Cog):
        embed = get_base_embed(
            title=f"Cog Help: {cog.qualified_name}",
            description=cog.description,
            color=self.color,
            author=ctx.me,
            footer_icon=ctx.me,
            footer_text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group"
        )

        cmds = cog.get_commands()
        if len(cmds) > 0:
            embed.add_field(
                name="Commands",
                value=", ".join(sorted([f"`{command.name}`" for command in cmds])),
                inline=False
            )
        
        return embed

    async def send_bot_help(self, mapping):
        embed = await self.get_bot_help_embed(self.context, mapping)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = self.get_command_help_embed(self.context, command)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = self.get_group_help_embed(self.context, group)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = self.get_cog_help_embed(self.context, cog)
        await self.get_destination().send(embed=embed)

    async def on_help_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            embed = get_base_embed(
                title="Error",
                description=str(error),
                author=ctx.me
            )
            await ctx.send(embed=embed)
        else:
            raise error

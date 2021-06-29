import discord
from discord.ext import commands
from .embed import Embed
from .utils import get_image_url


class HelpCommand(commands.HelpCommand):
    def __init__(self, color: discord.Color):
        self.color = color
        super().__init__()

    def get_command_signature(self, command: commands.Command):
        return f"`" + f"{self.clean_prefix}{command.qualified_name} {command.signature}".strip() + "`"

    async def send_bot_help(self, mapping):
        embed = Embed(
            title="Help",
            color=self.color,
            author=self.context.me
        )

        embed.set_footer(
            text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group",
            icon_url=get_image_url(self.context.me)
        )

        for cog, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = Embed(
            title=f"Command Help: {command.name}",
            description=command.help if command.help is not None else "None",
            color=self.color,
            author=self.context.me
        )

        embed.set_footer(
            text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group",
            icon_url=get_image_url(self.context.me)
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

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = Embed(
            title=f"Group Help: {group.name}",
            description=group.help,
            color=self.color,
            author=self.context.me
        )

        embed.set_footer(
            text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group",
            icon_url=get_image_url(self.context.me)
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
                name="Subcommands/subgroups",
                value=", ".join(sorted([f"`{command.name}`" for command in group.commands], key=lambda s: s)),
                inline=False
            )
        
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = Embed(
            title=f"Cog Help: {cog.qualified_name}",
            description=cog.description,
            color=self.color,
            author=self.context.me
        )

        embed.set_footer(
            text=f"Run {self.clean_prefix}help <command> to get more information about a command or command group",
            icon_url=get_image_url(self.context.me)
        )

        cmds = cog.get_commands()
        if len(cmds) > 0:
            embed.add_field(
                name="Commands",
                value=", ".join(sorted([f"`{command.name}`" for command in cmds])),
                inline=False
            )
        

        await self.get_destination().send(embed=embed)

    async def on_help_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            embed = Embed(
                title="Error",
                description=str(error),
                author=ctx.me
            )
            await ctx.send(embed=embed)
        else:
            raise error

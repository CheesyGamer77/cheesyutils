from discord.ext import commands


class ArgumentParsingError(commands.BadArgument):
    """Raised when a converter fails to convert a given argument

    This inherits from `discord.ext.commands.BadArgument`

    Attributes
    ----------
    argument : str
        The argument that failed to be converted
    """

    def __init__(self, argument: str, *args, **kwargs):
        self.argument = argument
        super().__init__(*args, **kwargs)

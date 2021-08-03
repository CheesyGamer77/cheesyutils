from discord.ext import commands
from typing import Optional


class ConversionFailed(commands.BadArgument):
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


class RangedConstraintFailure(ConversionFailed):
    """Raised when a value fails to satisfy a range constraint
    
    This inherits from `ConversionFailed`

    Attributes
    ----------
    argument : str
        The raw argument supplied
    minimum : int | None
        The minimum value required, or `None` if no minimum was specified
    maximum : int | None
        The maximum value required, or `None` if no maximum was specified
    """

    def __init__(self, argument: str, minimum: int=None, maximum: int=None):
        super().__init__(argument)
        self.minimum: Optional[int] = minimum
        self.maximum: Optional[int] = maximum


class IntegerRequired(ConversionFailed):
    """Raised when a integer parameter is required instead of another type

    Usually raised by the `RangedInteger` converter
    """

    pass


class PromptError(commands.CommandError):
    """Base class for all errors relating to prompts
    
    This inherits from `discord.ext.commands.CommandError`
    """

    pass


class PromptTimedout(PromptError):
    """Raised when a prommpt timed out

    Attributes
    ----------
    timeout : float
        The duration of the timeout
    """

    def __init__(self, timeout: float, *args, **kwargs):
        super().__init__()
        self.timeout = timeout

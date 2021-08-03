import discord
from discord.ext import commands
from .context import Context
from typing import Optional
from .errors import RangedConstraintFailure, IntegerRequired


class RangedInteger(commands.Converter):
    """Converter to serve as input validation for ranged integers

    The range can be specified as a minimum and maximum, as well as
    only a minimum or only a maximum. Not supplying one or both
    a minimum or a maximum will raise `ValueError`.

    The range specified is check as if the number is between
    a minimum and a maximum *inclusive*.

    This converter is required to be instantiated, such as the following example
    ```py
    @commands.command()
    async def test(self, ctx, integer: RangedInteger(minimum=0, maximum=3)):
        # this will only accept an integer between 0 and 3
        ...
    ```

    Attributes
    ----------
    minimum : int | None
        The minimum value required.
        If this is `None`, the value provided will only be
        checked against the `maximum`.
    maximum : int | None
        The maximum value required.
        If this is `None`, the value provided will only be
        checked against the `minimum`.
    
    Raises
    ------
    `RangedConstraintFailure` if the argument did not satisfy the range supplied.
    """

    def __init__(self, *, minimum: int=None, maximum: int=None):
        if minimum is None and maximum is None:
            raise ValueError("Range required for RangedInteger")

        self.minimum: Optional[int] = minimum
        self.maximum: Optional[int] = maximum
    
    async def convert(self, ctx: Context, argument: str):
        try:
            arg = int(argument)
        except ValueError:
            raise IntegerRequired
        
        if self.minimum is not None and self.maximum is not None:
            # minimum and maximum set
            constrained = self.minimum <= arg <= self.maximum
        elif self.minimum is None and self.maximum is not None:
            # no minimum set
            constrained = arg <= self.maximum
        else:
            # no maximum set
            constrained = self.minimum <= arg

        if not constrained:
            raise RangedConstraintFailure(arg, self.minimum, self.maximum)

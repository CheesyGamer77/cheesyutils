from enum import Enum
from .errors import ConversionFailed
from .context import Context


class NameConvertibleEnum(Enum):
    """Base class for enum converters

    The converter works by attempting to convert the given argument into an enum member.
    In the event that this fails, `ConversionFailed` is raised.

    Usage of this class typically comprises of the following child class and command examples
    ```py
    class ExampleEnum(NameConvertibleEnum):
        # this enum accepts "a", "b", and "c" as valid arguments
        a = 0
        b = 1
        c = 2

    @commands.command(name="test")
    async def test_command(self, ctx, arg: ExampleEnum):
        ...
    ```
    """
    
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> "NameConvertibleEnum":
        """
        Converts a given argument to the given enum.

        This will always raise `ConversionFailed` for enums with no members

        Parameters
        ----------
        ctx : Context
            The invokation context
        argument : str
            The argument to convert
        
        Raises
        ------
        `ConversionFailed` if a value passed could not be converted to an enum
        """
        
        try:
            return getattr(cls, argument)
        except ValueError:
            raise ConversionFailed(argument, f"{argument!r} is not a valid selection")

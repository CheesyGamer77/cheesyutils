import datetime
import discord
from dateutil.relativedelta import relativedelta
from discord.ext import commands
from typing import Any, List, Optional, Union
from enum import Enum


def get_discord_color(color: Union[discord.Color, tuple, str]) -> discord.Color:
    """Returns a discord.Color from an RGB tuple or hex string
    
    The hex string parsing is case insensitive

    Parameters
    ----------
    color: Union(discord.Color, tuple, str)

    Raises
    ------
    TypeError if the color was not a discord.Color, tuple, or string

    Returns
    -------
    A discord.Color object
    """

    if type(color) is tuple:
        # assuming it's RGB
        return discord.Color.from_rgb(color[0], color[1], color[2])
    elif type(color) is str:
        # code snippet taken from https://stackoverflow.com/a/29643643
        return get_discord_color(tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)))
    elif isinstance(color, (discord.Color, discord.Colour)):
        return color
    else:
        raise TypeError("Invalid Color type. Must be discord.Color, RGB tuple, or hex string")


def get_image_url(entity: Union[discord.abc.User, discord.Guild, discord.Asset, str]):
    """Returns an image url depending on if the desired entity is a User, Guild, or string

    Parameters
    ----------
    entity : Union(discord.abc.User, discord.Guild, discord.Asset, str)
        The entity to get the image url from
    
    Returns
    -------
    The image url as a string, or the entity itself if its already a string
    """

    if isinstance(entity, (discord.abc.User, discord.Guild, discord.Asset, str)):
        if isinstance(entity, discord.abc.User):
            return str(entity.avatar_url)
        elif isinstance(entity, discord.Guild):
            return str(entity.icon_url)
        elif isinstance(entity, discord.Asset):
            return str(entity)

        return entity
    else:
        raise TypeError(f"Expected discord.abc.User, discord.Guild, or string, got \"{entity.__class__.__name__}\" instead")


def role_permissions_in(channel: discord.abc.GuildChannel, role: discord.Role) -> discord.Permissions:
    """Returns a role's permissions in a particular channel

    This function is based off of a previous solution for gathering role channel permissions.
    Original Solution: https://gist.github.com/e-Lisae/f20c579ab70304a73506e5565631b753

    Parameters
    ----------
    channel : discord.abc.GuildChannel
        The channel to get the role's permissions for
    role : discord.Role
        The role to get the permissions for
    
    Returns
    -------
    A `discord.Permissions` object representing the role's permissions
    """

    # gather base permissions
    permissions = discord.Permissions.none()
    permissions.value |= role.permissions.value

    # merge with role permission overwrites
    pair = channel.overwrites_for(role).pair()
    permissions.value = (permissions.value & ~pair[1].value) | pair[0].value

    return permissions


def truncate(string: str, max_length: int, end: Optional[str] = "...") -> str:
    """Truncates a string

    Parameters
    ----------
    string : str
        The string to truncate, if needed
    max_length : int
        The maximum length of the string before truncation is needed
    end : Optional str
        The string to append to the end of the string after truncation
        The string is automatically downsized to accommodate the size of `end`
        This automatically defaults to "..."
    
    Raises
    ------
    ValueError
        If the size of `end` is larger than `max_length`

    Returns
    -------
    The truncated string
    """

    if len(end) > max_length:
        raise ValueError(f"End string \"{end}\" of length {len(end)} can't be larger than {max_length} characters")
    
    truncated = string[:max_length]
    if string != truncated:
        truncated = string[:max_length - len(end)] + end

    return truncated


def chunkify_string(string: str, max_length: int) -> List[str]:
    """Returns a list of strings of a particular maximum length
    
    Original solution taken from https://stackoverflow.com/a/18854817

    Parameters
    ----------
    string : str
        The string to slice
    max_length : int
        The maximum length for each string slice
    
    Returns
    -------
    A list of strings with maximum length of `max_length`
    """

    return [string[0+i:max_length+i] for i in range(0, len(string), max_length)]

class plural:
    """
    Helper class to convert a particular value to a plural form, if needed

    Original solution comes from RoboDanny
    (https://github.com/Rapptz/RoboDanny/blob/0dfa21599da76e84c2f8e7fde0c132ec93c840a8/cogs/utils/formats.py#L1-L10)
    """

    def __init__(self, value: Any):
        self.value = value
    def __format__(self, format_spec: str):
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        v = self.value
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'

def human_timedelta(dt: datetime.datetime, *, source: datetime.datetime=None, accuracy: int=3, brief: bool=False, suffix: bool=True) -> str:
    """
    Returns a human readable time delta since a particular datetime object
    Original solution comes from RoboDanny
    (https://github.com/Rapptz/RoboDanny/blob/0dfa21599da76e84c2f8e7fde0c132ec93c840a8/cogs/utils/time.py#L185-L284)

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object to get the human time delta since
    source : datetime.datetime
        The source datetime object to use as the latest point in time for the time delta
        This defaults to the current UTC time.
    accuracy: int
        The desired accuracy for the time delta. The number of desired time units to provide corresponds to the accuracy given
        This defaults to `3`
    brief : bool
        If `True`, only provides each time unit's count for the output, and not the time units themselves
        This defaults to `False`
    suffix : bool
        Whether to include the "ago" suffix in the output for past time deltas
        This defaults to `True`
    
    Returns
    -------
    A string representing the human readable time delta
    """

    def human_join(seq, delim=', ', final='or'):
        size = len(seq)
        if size == 0:
            return ''

        if size == 1:
            return seq[0]

        if size == 2:
            return f'{seq[0]} {final} {seq[1]}'

        return delim.join(seq[:-1]) + f' {final} {seq[-1]}'

    now = source or datetime.datetime.utcnow()
    # Microsecond free zone
    now = now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)

    # This implementation uses relativedelta instead of the much more obvious
    # divmod approach with seconds because the seconds approach is not entirely
    # accurate once you go over 1 week in terms of accuracy since you have to
    # hardcode a month as 30 or 31 days.
    # A query like "11 months" can be interpreted as "!1 months and 6 days"
    if dt > now:
        delta = relativedelta(dt, now)
        suffix = ''
    else:
        delta = relativedelta(now, dt)
        suffix = ' ago' if suffix else ''

    attrs = [
        ('year', 'y'),
        ('month', 'mo'),
        ('day', 'd'),
        ('hour', 'h'),
        ('minute', 'm'),
        ('second', 's'),
    ]

    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + 's')
        if not elem:
            continue

        if attr == 'day':
            weeks = delta.weeks
            if weeks:
                elem -= weeks * 7
                if not brief:
                    output.append(format(plural(weeks), 'week'))
                else:
                    output.append(f'{weeks}w')

        if elem <= 0:
            continue

        if brief:
            output.append(f'{elem}{brief_attr}')
        else:
            output.append(format(plural(elem), attr))

    if accuracy is not None:
        output = output[:accuracy]

    if len(output) == 0:
        return 'now'
    else:
        if not brief:
            return human_join(output, final='and') + suffix
        else:
            return ' '.join(output) + suffix


class TimestampStyle(Enum):
    """
    https://discord.com/developers/docs/reference#message-formatting-timestamp-styles
    """

    short_time = "t"
    long_time = "T"
    short_date = "d"
    long_date = "D"
    short_date_time = "f" # default
    long_date_time = "F"
    relative = "R"


def get_timestamp_mention(dt: datetime.datetime, *, style: TimestampStyle=None) -> str:
    """Returns a timestamp mention corresponding to a particular datetime object.

    A style may be optionally provided.
    
    Parameters
    ----------
    dt: datetime.datetime
        The datetime object to use for the timestamp mention
    style : TimestampStyle
        Optional style to use for the mention.
        This defaults to `TimestampStyle.short_date_time`
    
    Returns
    -------
    A timestamp mention string for the datetime object
    """

    if not style:
        style = TimestampStyle.short_date_time
    
    return f"<t:{int(dt.timestamp())}:{style.value}>"

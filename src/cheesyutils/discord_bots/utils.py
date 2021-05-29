import datetime
import discord
from discord.ext import commands
from typing import List, Optional, Union
from .constants import *


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


def get_base_embed(
    title: Optional[str] = discord.Embed.Empty,
    description: Optional[str] = discord.Embed.Empty,
    color: Optional[Union[discord.Color, tuple, str]] = discord.Color.dark_theme(),
    timestamp: Optional[Union[datetime.datetime, discord.Member, discord.Object]] = None,
    author: Optional[Union[discord.abc.User, discord.Guild]] = None,
    author_name: Optional[str] = None,
    author_icon: Optional[Union[discord.abc.User, discord.Guild, str]] = discord.Embed.Empty,
    author_url: Optional[str] = discord.Embed.Empty,
    thumbnail: Optional[Union[discord.abc.User, discord.Guild, str]] = None,
    image: Optional[Union[discord.abc.User, discord.Guild, str]] = None,
    footer: Optional[Union[discord.abc.User, discord.Guild]] = None,
    footer_text: Optional[str] = discord.Embed.Empty,
    footer_icon: Optional[Union[discord.abc.User, discord.Guild, str]] = discord.Embed.Empty,
    url: Optional[str] = discord.Embed.Empty,
) -> discord.Embed:
    """Returns a "base" embed without any fields

    This function automatically truncates any excess characters for each field with "..."

    Parameters
    ----------
    title : Optional str
        The embed title
    description : Optional str
        The embed description
    color : Optional Union(discord.Color, tuple, str)
        The color to use for the embed. Can be a `discord.Color` object, RGB tuple, or hex string.
        Defaults to `discord.Color.dark_theme()`
    timestamp : Optional Union(datetime.datetime, discord.Member, discord.Object)
        The utc timestamp, Discord member, or the Discord object to use for the embed.
        If a `discord.Object` is supplied, the timestamp used will be the object's `created_at` timestamp.
        If a `discord.Member` is supplied, the timestamp used will be the member's `joined_at` timestamp.
        This defaults to the current UTC timestamp if none of the above are supplied
    author : Optional Union(discord.abc.User, discord.Guild)
        The user or guild to use for the embed author name/icon. This overrides both `author_name` and `author_icon`
    author_name : Optional str
        The string to use for the embed author name
    author_icon : Optional str
        The url to use for the embed author icon
    author_url : Optional str
        The url to use for the embed author (for when the author name is clicked)
    thumbnail : Optional Union(discord.abc.User, discord.Guild, str)
        The url of the image to use for the embed thumbnail
    image : Optional Union(discord.abc.User, discord.Guild, str)
        The url of the image to use for the embed image
    footer : Optional Union(discord.abc.User, discord.Guild)
        The user or guild to use for the embed footer text/icon. This overrides both `footer_text` and `footer_icon`
    footer_text : Optional str
        The string to use for the footer text
    footer_icon : Optional Union(discord.abc.User, discord.Guild)
        The url to use for the embed footer icon
    url : Optional str
        The url to use for the embed (for when the title is clicked)

    Raises
    ------
    ValueError
        - If the total embed character limit of 6000 characters is exceeded after attempting to truncate the embed title,
        description, footer text, and author_name
        - If all fields are empty
    
    Returns
    -------
    A discord.Embed from the provided attributes, without any embed fields
    """

    Empty = discord.Embed.Empty

    # check if all None
    if title is Empty and description is Empty and color is Empty and author is None and author_name is None and thumbnail is None and image is None and footer is None and footer_text is Empty and footer_icon is Empty and url is None:
        raise ValueError("Cannot construct an empty base embed")

    # convert timestamp to either a Discord member's joined_at or another Discord object's created_at timestamp
    if isinstance(timestamp, discord.Member):
        timestamp = timestamp.joined_at
    elif isinstance(timestamp, discord.Object):
        timestamp = discord.utils.snowflake_time(timestamp.id)
    elif timestamp is None:
        timestamp = datetime.datetime.utcnow()

    # set author icon
    if author_icon is not Empty:
        author_icon = get_image_url(author_icon)

    # override author attributes
    if author is not None:
        author_name = str(author)
        author_icon = author.avatar_url if isinstance(author, discord.abc.User) else author.icon_url
    
    # set footer icon
    if footer_icon is not Empty:
        footer_icon = get_image_url(footer_icon)

    # override footer attributes
    if footer is not None:
        footer_text = str(footer)
        footer_icon = footer.avatar_url if isinstance(footer, discord.abc.User) else footer.icon_url

    # truncate neccessary fields
    title = truncate(title, MAX_EMBED_TITLE_LENGTH) if title is not discord.Embed.Empty else discord.Embed.Empty
    description = truncate(description, MAX_EMBED_DESCRIPTION_LENGTH) if description is not discord.Embed.Empty else discord.Embed.Empty
    footer_text = truncate(footer_text, MAX_EMBED_FOOTER_TEXT_LENGTH) if footer_text is not Empty else Empty
    author_name = truncate(author_name, MAX_EMBED_AUTHOR_NAME_LENGTH) if author_name is not None else None

    # construct embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=get_discord_color(color),
        timestamp=timestamp,
        url=url,
    )

    # set embed author
    if author_name is not None:
        embed.set_author(
            name=author_name,
            icon_url=author_icon,
            url=author_url
        )
    
    # set embed footer
    if footer_text is not Empty:
        embed.set_footer(
            text=footer_text
        )
    
    if footer_icon is not Empty:
        embed.set_footer(
            icon_url=footer_icon
        )
    
    # set embed thumbnail
    if thumbnail is not None:
        embed.set_thumbnail(get_image_url(thumbnail))
    
    # set embed image
    if image is not None:
        embed.set_image(get_image_url(image))
    
    # check max length
    if len(embed) > MAX_EMBED_TOTAL_LENGTH:
        raise ValueError(f"Base embed character count of {len(embed)} is over limit of {MAX_EMBED_TOTAL_LENGTH}")
    
    return embed


async def paginate(
    ctx: commands.Context,
    embed_title: str,
    line: str,
    sequence: list,
    embed_color: discord.Color = discord.Color.dark_theme(),
    prefix: str = "",
    suffix: str = "",
    max_page_size: int = 2048,
    other_sequence: list = None,
    sequence_type_name: str = None,
    author_name: str = None,
    author_icon_url: str = None,
    count_format: str = None
):
    """Creates a paginating menu given a particular context

    Warning: The following permissions are required for the bot to utilize pagination
    - Add Reactions
    - Manage Messages

    Parameters
    ----------
    ctx : commands.Context
        The context in which the pagination is to take place
    embed_title : str
        The title to use for the embed
    line : str
        The format string to use for each line in a page. Each item in `sequence` gets its own line in a page
    sequence : list
        The sequence in which pagination should take place
    embed_color : Optional discord.Color
        The embed color to use. Defaults to `discord.Color.dark_theme()`
    prefix : Optional str
        The string to prepend to the beginning of the page (defaults to an empty string)
    suffix : Optional str
        The string to append to the end of the page (defaults to an empty string)
    max_page_size : Optional int
        The maximum number of characters per page (defaults to 2048)
    other_sequence : Optional list
        The other sequence to iterate over (mainly for the embed's footer text, defaults to be equal to `sequence`)
    sequence_type_name : Optional str
        The name of the other sequence (mainly for the embed's footer text, defaults to "items")
    author_name : Optional str
        The name to use for the embed author (defaults to the current guild's name)
    author_icon_url : Optional str
        The icon url to use for the embed author (defaults to the current guild's icon)
    count_format : Optional str
        The string to prepend to each line (used for a count)
    """

    if other_sequence is None:
        other_sequence = sequence
        sequence_type_name = "items" if sequence_type_name is None else sequence_type_name

    far_left = "⏮"
    left = '⏪'
    right = '⏩'
    far_right = "⏭"

    def predicate(m: discord.Message, set_begin: bool, push_left: bool, push_right: bool, set_end: bool):
        def check(reaction: discord.Reaction, user: discord.User):
            if reaction.message.id != m.id or user.id == ctx.bot.user.id or user.id != ctx.author.id:
                return False
            if set_begin and reaction.emoji == far_left:
                return True
            if push_left and reaction.emoji == left:
                return True
            if push_right and reaction.emoji == right:
                return True
            if set_end and reaction.emoji == far_right:
                return True

            return False

        return check

    # init paginator
    paginator = commands.Paginator(prefix=prefix, suffix=suffix, max_size=max_page_size)

    item_count = 0
    for item in sequence:
        item_count += 1
        if count_format is not None:
            paginator.add_line(
                line=(count_format.format(item_count) + line.format(item))
            )
        else:
            paginator.add_line(
                line=line.format(item)
            )

    index = 0
    message = None
    action = ctx.send
    while True:
        embed = discord.Embed(
            title=embed_title,
            description=paginator.pages[index],
            color=embed_color,
            timestamp=datetime.datetime.utcnow()
        )

        if author_name is None:
            author_name = ctx.guild.name
        
        if author_icon_url is None:
            author_icon_url = ctx.guild.icon_url

        embed.set_author(
            name=author_name,
            icon_url=author_icon_url
        )

        embed.set_footer(
            text=f"Page {index + 1}/{len(paginator.pages)} • "
                    f"{len(sequence)}/{len(other_sequence)} {sequence_type_name}"
        )

        res = await action(embed=embed)

        if res is not None:
            message = res

        await message.clear_reactions()

        # determine which emojis should be added
        set_begin = index > 1
        push_left = index != 0
        push_right = index != len(paginator.pages) - 1
        set_end = index < len(paginator.pages) - 2

        # add the appropriate emojis
        if set_begin:
            await message.add_reaction(far_left)
        if push_left:
            await message.add_reaction(left)
        if push_right:
            await message.add_reaction(right)
        if set_end:
            await message.add_reaction(far_right)

        # wait for reaction and set page index
        react, usr = await ctx.bot.wait_for(
            "reaction_add", check=predicate(message, set_begin, push_left, push_right, set_end)
        )

        if react.emoji == far_left:
            index = 0
        elif react.emoji == left:
            index -= 1
        elif react.emoji == right:
            index += 1
        elif react.emoji == far_right:
            index = len(paginator.pages) - 1

        action = message.edit

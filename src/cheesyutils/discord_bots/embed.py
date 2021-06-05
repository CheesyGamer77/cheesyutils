import discord
from .constants import *
from .utils import chunkify_string
from typing import Any, Union


class Embed(discord.Embed):
    def __init__(self, **kwargs):
        author = kwargs.pop("author", None)
        footer = kwargs.pop("footer", None)
        thumbnail = kwargs.pop("thumbnail", None)
        image = kwargs.pop("image", None)

        super().__init__(**kwargs)

        if author:
            self.set_author_from_entity(author)
        if footer:
            self.set_footer_from_entity(footer)
        if thumbnail:
            self.set_image(url=thumbnail)
        if image:
            self.set_image(url=image)

    def _check_integrety(self):
        if len(self) > MAX_EMBED_TOTAL_LENGTH:
            raise ValueError(f"Embed total length cannot exceed {MAX_EMBED_TOTAL_LENGTH} in length")
        elif len(self.title) > MAX_EMBED_TITLE_LENGTH:
            raise ValueError(f"Embed title cannot exceed {MAX_EMBED_TITLE_LENGTH} in length")
        elif len(self.description) > MAX_EMBED_DESCRIPTION_LENGTH:
            raise ValueError(f"Embed description cannot exceed {MAX_EMBED_DESCRIPTION_LENGTH} in length")
        elif len(self.fields) > MAX_EMBED_FIELD_COUNT:
            raise ValueError(f"Embed field count cannot exceed {MAX_EMBED_FIELD_COUNT}")
    
    @property
    def colour(self):
        return super().colour
    
    @colour.setter
    def colour(self, value: Union[discord.Colour, int, discord.User, discord.Member]):
        if isinstance(value, (discord.Colour, discord.embeds._EmptyEmbed)):
            self._colour = value
        elif isinstance(value, int):
            self._colour = discord.Colour(value=value)
        elif isinstance(value, (discord.User, discord.Member)):
            self._colour = value.color
        else:
            raise TypeError('Expected discord.Colour, int, discord.Member, discord.User, or Embed.Empty but received %s instead.' % value.__class__.__name__)

    def set_footer_from_entity(self, entity: Union[discord.User, discord.Member, discord.Guild]):
        """Sets this embed footer from a particular Discord entity. For general usage, refer to the `set_footer` function.

        If this is a discord.User or discord.Member, the footer will be of the user's name and avatar.
        If this is a discord.Guild, the footer will be of the guild's name and icon.
        Otherwise, this will raise a `ValueError`.

        This function returns the class instance for fluent-style chaining.

        Parameters
        ----------
        entity : Union(discord.User, discord.Member, discord.Guild)
            The entity to set the footer from.
        
        Raises
        ------
        `ValueError` if an invalid entity type was supplied.

        Returns
        -------
        The class instance.
        """

        if isinstance(entity, (discord.User, discord.Member)):
            return self.set_footer(text=str(entity), icon_url=entity.avatar_url)
        elif isinstance(entity, discord.Guild):
            return self.set_footer(text=entity.name, icon_url=entity.icon_url)
        else:
            raise ValueError(f"Expected a discord.User, discord.Member, or discord.Guild but received {entity.__class__.__name__} instead")

    def set_footer(self, *, text: str=discord.embeds._EmptyEmbed, icon_url: str=discord.embeds._EmptyEmbed) -> "Embed":
        if text is not discord.embeds._EmptyEmbed:
            if len(text) > MAX_EMBED_FOOTER_TEXT_LENGTH:
                raise ValueError(f"Embed field text cannot exceed {MAX_EMBED_FOOTER_TEXT_LENGTH} in length")
        return super().set_footer(text=text, icon_url=icon_url)

    def set_image(self, *, url) -> "Embed":
        """Sets the image for this particular embed.

        If the url supplied is a `discord.User` or `discord.Member`, the url will be converted to the user's/member's avatar.
        If the url supplied is a `discord.Guild`, the url will be converted to the guild's icon url.

        This function returns the class instance for fluent-style chaining.

        Parameters
        ----------
        url : Any
            The url to use for the image. Only HTTP(S) is supported
        
        Returns
        -------
        The class instance.
        """

        if isinstance(url, (discord.User, discord.Member)):
            url = url.avatar_url
        elif isinstance(url, discord.Guild):
            url = url.icon_url

        return super().set_image(url)
    
    def set_thumbnail(self, *, url) -> "Embed":
        """Sets the thumbnail image for this particular embed.

        If the url supplied is a `discord.User` or `discord.Member`, the url will be converted to the user's/member's avatar.
        If the url supplied is a `discord.Guild`, the url will be converted to the guild's icon url.

        This function returns the class instance for fluent-style chaining.

        Parameters
        ----------
        url : Any
            The url to use for the thumbnail image. Only HTTP(S) is supported
        
        Returns
        -------
        The class instance.
        """

        return super().set_thumbnail(url)

    def set_author(self, *, name, url=discord.embeds._EmptyEmbed, icon_url=discord.embeds._EmptyEmbed) -> "Embed":
        if len(name) > MAX_EMBED_AUTHOR_NAME_LENGTH:
            raise ValueError(f"Embed author name cannot exceed {MAX_EMBED_AUTHOR_NAME_LENGTH} characters in length")
    
        e = super().set_author(name=name, url=url, icon_url=icon_url)
        self._check_integrety()
        return e
    
    def set_author_from_entity(self, entity: Union[discord.User, discord.Member, discord.Guild]) -> "Embed":
        """Sets this embed's author from a particular Discord entity. For general usage, refer to the `set_author` function.

        If this is a `discord.User` or `discord.Member`, the author will be of the user's name and avatar.
        If this is a `discord.Guild`, the author will be of the guild's name and icon.
        Otherwise, this will raise a `ValueError`.

        This function returns the class instance to allow for fluent-style chaining.

        Parameters
        ----------
        entity : Union(discord.User, discord.Member, discord.Guild)
            The Discord entity to set the embed author from.
        
        Raises
        ------
        `ValueError` if an invalid entity type was supplied.

        Returns
        -------
        The class instance.
        """

        if isinstance(entity, (discord.User, discord.Member)):
            return self.set_author(name=str(entity), icon_url=entity.avatar_url)
        elif isinstance(entity, discord.Guild):
            return self.set_author(name=entity.name, icon_url=entity.icon_url)
        else:
            raise ValueError(f"Expected a discord.User, discord.Member, or discord.Guild but received {entity.__class__.__name__} instead")
    
    def add_field(self, *, name: str, value: Any, inline: bool=True) -> "Embed":
        e = super().add_field(name, value, inline=inline)
        self._check_integrety()
        return e
    
    def add_fields(self, base_name: str, name_fmt: str, value: str, inline: bool=True) -> "Embed":
        """Adds one or more fields depending on how long a given text is.

        This is useful when you want to set an embed field to a string potentially longer than the maximum allowed
        length for embed field values.

        This function returns the class instance to allow for fluent-style chaining.

        Parameters
        ----------
        base_name: str
            The name to use for the first field to be added.
            The embed's current additional field number followed by the embed's total fields
            to be added will be attempted to be formatted.
        name_fmt: str
            The name format to use for each field that is added after the first field.
            The embed's current additional field number followed by the embed's total fields to be added
            will always be attempted to be formatted.
        value: str
            The value to split in between multiple fields if deemed neccesary.
        inline: bool
            Whether each field to be added is inline or not.
            This defaults to `True`.
        
        Returns
        -------
        The class instance.
        """
        
        chunks = chunkify_string(value, MAX_EMBED_FIELD_VALUE_LENGTH)
        total_chunks = len(chunks)
        fields_remaining = MAX_EMBED_FIELD_COUNT - (len(self.fields) + total_chunks)
        if fields_remaining >= 0:
            for i, chunk in enumerate(chunks):
                if i == 0:
                    name = base_name
                else:
                    name = name_fmt

                self.add_field(
                    name=name.format(i+1, total_chunks),
                    value=chunk,
                    inline=inline
                )
            return self
        else:
            raise ValueError(f"Cannot add embed fields (not enough embed fields remaining)")

    def insert_field_at(self, index, *, name, value, inline) -> "Embed":
        e = super().insert_field_at(index, name, value, inline=inline)
        self._check_integrety()
        return e
    
    def set_field_at(self, index, *, name, value, inline):
        e = super().set_field_at(index, name, value, inline=inline)
        self._check_integrety()
        return e
    
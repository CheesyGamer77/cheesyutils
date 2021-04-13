import discord
from discord.ext import commands
from typing import Any, Iterator, Optional, Sequence


class Page:
    """Represents a single page in a paginator

    This class is not normally created manually. See the `Paginator class
    for your pagination needs

    Parameters
    ----------
    items : Sequence[any]
        The sequence to iterate over for the page
    line_sep : Optional str
        The line separator to join for each line
    prefix : Optional str
        The prefix to prepend at the beginning of the page's embed description
    suffix : Optional str
        The suffix to append at the end of the page's embed description
    
    Attributes
    ----------
    embed : discord.Embed
        The page's Discord Embed that will be sent in Discord for pagination
    """

    def __init__(self, items: Sequence[Any], line_sep: Optional[str] = "\n", prefix: Optional[str] = "```", suffix: Optional[str] = "```"):
        """Defines a new page for a paginator

        This class is typically not created manually. See the `Paginator` class
        for your pagination needs

        Parameters
        ----------

        """

        self.items = items
        self.line_sep = line_sep
        self.prefix = prefix
        self.suffix = suffix

    def __str__(self) -> str:
        """Returns the string to be used for this `Page`'s embed description

        Returns
        -------
        This `Page`'s embed description
        """

        return self.embed.description 

    @property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title="Page",
            description=self.line_sep.join([self.prefix, *[item for item in self.items], self.suffix])
        )


class Paginator:
    def __init__(self):
        self.pages = []

    def insert_page(self, index: int, page: Page):
        """Inserts a new page at a particular position in the paginator

        Prameters
        ---------
        page : Page
            The page to insert into the paginator
        """

        self.pages.insert(index, page)

    def prepend_page(self, page: Page):
        """Adds a new page to the beginning of the paginator's pages

        Prameters
        ---------
        page : Page
            The page to add to the beginning of the paginator
        """

        self.pages.insert(0, page)

    def add_page(self, page: Page):
        """Adds a new page to the end of the paginator's pages

        NOTE: Using this method assumes that you will be creating each page manually,
        ie. not via `Paginator.set_sequence`.
        """

        self.pages.append(page)

    def __iter__(self) -> Iterator[Page]:
        """Returns an interator to iterate through the paginator's pages

        Returns
        -------
        An iterator of `Page`s
        """

        return iter(self.pages)
    
    def __next__(self) -> Optional[Page]:
        """Returns the next page in the paginator

        Raises
        ------
        `StopIteration` when there are no more pages to paginate through

        Returns
        -------
        The next `Page`
        """

        return next(self.pages)

    def __len__(self) -> int:
        """Returns the number of pages for the paginator
        
        Returns
        -------
        An integer representing the number of pages the paginator has
        """

        return len(self.pages)

    @property
    def is_paginated(self) -> bool:
        """Returns whether the paginator is "paginated", meaning containing more than one page

        Returns
        -------
        `True` if the paginator contains more than one page, else `False`
        """

        return len(self) != 0

    def set_sequence(self, sequence: Sequence[Any]):
        """Sets the sequence to paginate

        TODO: This currently assumes that all sequences are two-dimensioned sequences

        NOTE: This overrrides all of the internal pages set. This means that even if you manually created your own pages
        using `Paginator.add_page()`, these pages will be overwritten.

        Parameters
        ----------
        sequence : Sequence(Any)
            The sequence to paginate
        """

        self.pages = [Page(item) for item in sequence]

    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True, manage_messages=True)
    async def paginate(self, ctx: commands.Context):
        """Starts the paginator in the given context

        NOTE: In order to paginate, your bot needs to have the
        following permissions in the given context:
        - Send Messages
        - Embed Links
        - Add Reactions
        - Manage Messages (for resetting pagination menu button reactions)
        """

        """
        if other_sequence is None:
            other_sequence = sequence
            sequence_type_name = "items" if sequence_type_name is None else sequence_type_name
        """

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
        
        """
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
        """

        index = 0
        message = None
        action = ctx.send
        while True:
            """
            # this is probably going to fuck shit up
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
            """

            res = await action(embed=self.pages[index].embed)

            if res is not None:
                message = res

            await message.clear_reactions()

            # determine which emojis should be added
            set_begin = index > 1
            push_left = index != 0
            push_right = index != len(self.pages) - 1
            set_end = index < len(self.pages) - 2

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
                index = len(self.pages) - 1
            else:
                await react.remove(usr)

            action = message.edit

    @classmethod
    def from_pages(cls, *pages: Sequence[Page]):
        """Creates a paginator from a given list of pages

        This allows for more lower level control than `Paginator.from_sequence`

        Parameters
        ----------
        pages : Sequence[Page]
            The list of pages to add to the list
        """

        c = cls()
        c.pages = pages
        return c

    @classmethod
    def from_sequence(cls, sequence: Sequence[Any]):
        """Creates a default paginator from a given sequence

        This mainly serves as a shortcut to creating a default `Paginator` object
        then setting the sequence seperately.

        Parameters
        ----------
        sequence : Sequence(Any)
            The sequence to create the paginator from
        
        Returns
        -------
        A `Paginator` with its sequence set to the given sequence
        """

        return cls().set_sequence(sequence)

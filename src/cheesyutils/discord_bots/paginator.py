import discord
from discord.ext import commands
from typing import Iterator, List, NoReturn, Optional, Sequence


class Paginator:
    def __init__(self):
        self.pages: List[discord.Embed] = []

    def insert_page_at(self, index: int, page: discord.Embed):
        """Inserts a new page at a particular position in the paginator

        Prameters
        ---------
        page : Page
            The page to insert into the paginator
        """

        self.pages.insert(index, page)

    def prepend_page(self, page: discord.Embed):
        """Adds a new page to the beginning of the paginator's pages

        Prameters
        ---------
        page : Page
            The page to add to the beginning of the paginator
        """

        self.pages.insert(0, page)

    def add_page(self, page: discord.Embed):
        """Adds a new page to the end of the paginator's pages

        NOTE: Using this method assumes that you will be creating each page manually,
        ie. not via `Paginator.set_sequence`.
        """

        self.pages.append(page)

    def __iter__(self) -> Iterator[discord.Embed]:
        """Returns an interator to iterate through the paginator's pages

        Returns
        -------
        An iterator of `Page`s
        """

        return iter(self.pages)
    
    def __next__(self) -> Optional[discord.Embed]:
        """Returns the next page in the paginator

        Raises
        ------
        `StopIteration` when there are no more pages to paginate through

        Returns
        -------
        The next `Page` in the pagination sequence
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

    async def paginate(self, ctx: commands.Context) -> NoReturn:
        """Starts the paginator in the given context

        NOTE: In order to paginate, your bot needs to have the
        following permissions in the given context:
        - Send Messages
        - Embed Links
        - Add Reactions
        - Manage Messages (for resetting pagination menu button reactions)

        If any of the above permissions are missing, this coroutine is exited silently

        Parameters
        ----------
        ctx : discord.commands.Context
            The invocation context
        """

        permissions: discord.Permissions = ctx.me.permissions_in(ctx.channel)
        if permissions.add_reactions and permissions.embed_links and permissions.send_messages and permissions.manage_messages:
            # set emojis
            far_left = "⏮"
            left = '⏪'
            right = '⏩'
            far_right = "⏭"

            # reaction check to be used later
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

            index = 0
            message = None
            action = ctx.send
            while True:
                res = await action(embed=self.pages[index])

                if res is not None:
                    message = res

                await message.clear_reactions()

                # determine which emojis should be added depending on how many pages are left in each direction
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

                # set next page index
                if react.emoji == far_left:
                    index = 0
                elif react.emoji == left:
                    index -= 1
                elif react.emoji == right:
                    index += 1
                elif react.emoji == far_right:
                    index = len(self.pages) - 1
                else:
                    # invalid reaction, remove it
                    await react.remove(usr)

                action = message.edit

    @classmethod
    def from_embeds(cls, *pages: Sequence[discord.Embed]):
        """Creates a paginator from a given list of embeds

        This allows for more lower level control than `Paginator.from_sequence`

        Parameters
        ----------
        pages : Sequence[discord.Embed]
            The list of pages to add to the list
        """

        c = cls()
        c.pages = pages
        return c

    @classmethod
    def from_sequence(cls, sequence: Sequence[str], max_lines: int=10):
        """Sets the sequence to paginate over

        The sequence provided will be spliced into sublists of a maximum size (with thanks to https://stackoverflow.com/a/9671301)

        Parameters
        ----------
        sequence : Sequence(str)
            The sequence of strings to paginate through. Each string is given it's own line in the paginator
        max_items : int
            The maximum number of items/lines to have on each page.
            This defaults to `10`.
        """

        def chunks(l, n):
            """
            Converts a sequence to a list of sub-lists of a maximum size

            The code for this function comes from https://stackoverflow.com/a/9671301

            Parameters
            ----------
            l : list
                The list to split into chunks
            n : int
                The maximum number of items for each sublist

            Returns
            -------
            A list of lists, with each sublist being of maximum size `n`
            """

            n = max(1, n)
            return (l[i:i+n] for i in range(0, len(l), n))

        c = cls()
        c.pages = [
            discord.Embed(title=f"Page {i+1}", description="\n".join([line for line in chunk]))
            for i, chunk in enumerate(chunks(sequence, max_lines))
        ]

        return c

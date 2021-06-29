import asyncio
import cachetools
from typing import Any


class AsyncWriteThroughLRUCache(cachetools.LRUCache):
    """Class for implementing an LRU write-through cache policy

    This class inherits from `cachetools.LRUCache`.

    This class acts morseo as an interface rather than as a functional implementation.
    This expects that child classes implement their own logic for the write-through part
    of the cache policy. The `on_write`, `on_miss`, and `on_evict` abstract coroutines are
    designated for this purpose.

    The `on_write` coroutine is called whenever a cache entry is written and/or updated.
    The `on_miss` coroutine is called whenever a cache miss occurs at a particular key.
    And the `on_evict` coroutine is called whenever a cache entry is evicted at a particular key.

    Attributes
    ----------
    loop : `asyncio.AbstractEventLoop`
        The event loop to use. This is required in order to dispatch
        the `on_write`, `on_miss`, and `on_evict` events.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop=None, **kwargs):
        """Defines a new async write-through LRU cache

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The event loop to use.
        **kwargs
            Other arguments to use for cache initiation. See `cachetools.LRUCache.__init__`
        """

        super().__init__(**kwargs)
        self.loop = loop if loop else asyncio.get_event_loop()
    
    def __getitem__(self, key: Any, cache_getitem=cachetools.Cache.__getitem__) -> Any:
        try:
            return super().__getitem__(key, cache_getitem)
        except KeyError:
            self.loop.create_task(self.on_miss(key))
    
    def __setitem__(self, key: Any, value: Any, cache_setitem=cachetools.Cache.__setitem__) -> None:
        super().__setitem__(key, value, cache_setitem=cache_setitem)
        self.loop.create_task(self.on_write(key, value))
    
    def __delitem__(self, key: Any, cache_delitem=cachetools.Cache.__delitem__) -> None:
        super().__delitem__(key, cache_delitem=cache_delitem)
        self.loop.create_task(self.on_evict(key))
    
    async def on_miss(self, key: Any):
        """Called whenever a cache miss at a particular key occurs

        Parameters
        ----------
        key : Any
            The key where the cache miss occured
        
        Raises
        ------
        `NotImplementedError`
            Child classes are required to implement this method
        """

        raise NotImplementedError

    async def on_write(self, key: Any, value: Any):
        """Called whenever a cache entry is written

        By the time this coroutine is called, the key/value pair
        has already been written into the cache itsself.

        Parameters
        ----------
        key : Any
            The key that was written to
        value : Any
            The value that was written

        Raises
        ------
        `NotImplementedError`
            Child classes are required to implement this method
        """

        raise NotImplementedError

    async def on_evict(self, key: Any):
        """Called whenever a cache entry is evicted

        By the time this coroutine is called, the key/value pair
        has already been evicted from the cache.

        Parameters
        ----------
        key : Any
            The key that was evicted

        Raises
        ------
        `NotImplementedError`
            Child classes are required to implement this method
        """

        raise NotImplementedError

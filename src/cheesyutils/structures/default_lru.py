import cachetools
from typing import Any


class DefaultLRUCache(cachetools.LRUCache):
    def __init__(self, default: Any=None, **kwargs):
        super().__init__(**kwargs)
        self.default = default

    def __getitem__(self, key, cache_getitem=cachetools.Cache.__getitem__) -> Any:
        try:
            return super().__getitem__(key, cache_getitem=cache_getitem)
        except KeyError:
            return self.default
    
    def __delitem__(self, key: Any, cache_delitem=cachetools.Cache.__delitem__) -> None:
        try:
            return super().__delitem__(key, cache_delitem=cache_delitem)
        except KeyError:
            pass
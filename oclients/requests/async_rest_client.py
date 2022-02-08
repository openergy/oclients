import functools
import concurrent

from .rest_client import RESTClient
from ..snippets.oasyncio import get_loop

_thread_pool = None  # shared between threads


def _get_thread_pool(max_threads_if_creation=None):
    """

    Parameters
    ----------
    max_threads_if_creation: must be >=1 or None (auto)
        will only be taken into account on pool creation
    """
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = concurrent.futures.ThreadPoolExecutor(max_threads_if_creation)
    return _thread_pool


def _coroutine_wrapper(sync_fct):
    async def _async_fct(*args, **kwargs):
        return await get_loop().run_in_executor(_get_thread_pool(), functools.partial(
            sync_fct,
            *args,
            **kwargs
        ))
    return _async_fct


class AsyncRESTClient:
    def __init__(self, host, port, credentials=None, root_endpoint="", is_on_resource="/", verify_ssl=True):
        self._sync_client = RESTClient(
            host,
            port,
            credentials=credentials,
            root_endpoint=root_endpoint,
            is_on_resource=is_on_resource,
            verify_ssl=verify_ssl
        )

    def __getattr__(self, item):
        """
        private methods are called sync, public async
        """
        if item[0] == "_":
            return getattr(self._sync_client, item)

        return _coroutine_wrapper(getattr(self._sync_client, item))

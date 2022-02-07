import functools
import asyncio
import concurrent

from .rest_client import RESTClient

_thread_pool = None  # shared between threads


def get_loop():
    """
    Rules :
    * 1 loop per thread (prevents from multiple run_until_compete on same loop in sync code)
    * 1 thread pool per process
    * 1 process pool per process
    """
    try:
        return asyncio.get_event_loop()
    except RuntimeError:  # in a thread, loop may not be set
        asyncio.set_event_loop(asyncio.new_event_loop())
        return asyncio.get_event_loop()


def get_thread_pool():
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = concurrent.futures.ThreadPoolExecutor()
    return _thread_pool


def _coroutine_wrapper(sync_fct):
    async def _async_fct(*args, **kwargs):
        return await get_loop().run_in_executor(get_thread_pool(), functools.partial(
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

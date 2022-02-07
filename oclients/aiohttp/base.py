import time
import asyncio

import aiohttp


class AiohttpClient:
    """
    Raises
    ------
    ClientResponseError
    """
    _WAIT_FREQ = 0.5

    def __init__(self, host, port, credentials=None, verify_ssl=True):
        """
        credentials: login, password
        """
        if "http" not in host:
            host = "http://%s" % host
        self.base_url = "%s:%s" % (host, port)
        tcp_connector = aiohttp.TCPConnector(verify_ssl=verify_ssl)
        self.session = aiohttp.ClientSession(loop=get_loop(), auth=credentials, connector=tcp_connector)

    @staticmethod
    async def check_rep(rep):
        if (rep.status // 100) != 2:
            raise exceptions.ClientResponseError(
                await rep.text(),
                rep.status,
                f"{rep.request_info.method} {rep.request_info.real_url.human_repr()}"
            )

    @classmethod
    async def rep_to_json(cls, rep):
        await cls.check_rep(rep)
        # we use our json loads for date parsing
        return json_loads(await rep.text())

    async def wait_for_on(self, timeout=10, freq=1):
        start = time.time()
        if timeout <= 0:
            raise ValueError
        while True:
            if (time.time() - start) > timeout:
                raise TimeoutError
            try:
                await self._check_is_on_request()
                break
            except (aiohttp.client_exceptions.ClientConnectorError, TimeoutError):
                pass
            await asyncio.sleep(freq)

    async def _check_is_on_request(self):
        raise NotImplementedError

import time

import requests
from requests import exceptions

from ..exceptions import ClientResponseError

from ..snippets.ojson import loads as json_loads


class RequestsClient:
    """
    Raises
    ------
    ClientResponseError
    """
    _WAIT_FREQ = 0.5

    def __init__(self, host, port, credentials=None, timeout=None):
        """
        credentials: login, password
        """
        if "http" not in host:
            host = "http://%s" % host

        self.base_url = "%s:%s" % (host, port)
        self.session = requests.Session()
        if credentials is not None:
            self.session.auth = credentials
        self.timeout = timeout

    @staticmethod
    def check_rep(rep):
        if (rep.status_code // 100) != 2:
            raise ClientResponseError(rep.text, rep.status_code, f"{rep.request.method} {rep.request.url}")

    @classmethod
    def rep_to_json(cls, rep):
        cls.check_rep(rep)
        # we use our json loads for date parsing
        return json_loads(rep.text)

    def wait_for_on(self, timeout=10, freq=1):
        start = time.time()
        if timeout <= 0:
            raise ValueError
        while True:
            if (time.time() - start) > timeout:
                raise TimeoutError
            try:
                self._check_is_on_request()
                break
            except (exceptions.ConnectionError, TimeoutError):
                pass
            time.sleep(freq)

    def _check_is_on_request(self):
        raise NotImplementedError

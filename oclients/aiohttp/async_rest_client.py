from multidict import MultiDict

from .base import AiohttpClient

from ..snippets.odatetime import ISO_FORMAT
from ..snippets.ojson import dumps as json_dumps


class RESTClient(AiohttpClient):
    def __init__(self, host, port, credentials=None, root_endpoint="", is_on_resource="/", verify_ssl=True):
        """
        is_on_resource: put None if you don't want to use it
        """
        super().__init__(host, port, credentials=credentials, verify_ssl=verify_ssl)
        self.base_endpoint_url = self.base_url + "/" + root_endpoint.strip("/")
        self._is_on_request = is_on_resource
        self.verify_ssl = verify_ssl

    async def list(self, resource, params=None):
        resource = resource.strip("/")
        params = self._encode_dict(params)
        async with self.session.get("%s/%s/" % (self.base_endpoint_url, resource), params=params) as rep:
            return await self.rep_to_json(rep)

    async def list_iter_all(self, resource, params=None):
        start = 0
        if params is None:
            params = {}
        while True:
            params["start"] = start
            current = await self.list(resource, params=params)
            data = current["data"]
            if len(data) == 0:  # todo: should not need to perform last request
                break
            start += len(data)
            for element in data:
                yield element

    async def retrieve(self, resource, resource_id):
        resource = resource.strip("/")
        async with self.session.get("%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id)) as rep:
            return await self.rep_to_json(rep)

    async def create(self, resource, data):
        resource = resource.strip("/")
        async with self.session.post("%s/%s/" % (self.base_endpoint_url, resource), json=data) as rep:
            return await self.rep_to_json(rep)

    async def partial_update(self, resource, resource_id, data):
        resource = resource.strip("/")
        async with self.session.patch("%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id), json=data) as rep:
            return await self.rep_to_json(rep)

    async def update(self, resource, resource_id, data):
        resource = resource.strip("/")
        async with self.session.put("%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id), json=data) as rep:
            return await self.rep_to_json(rep)

    async def detail_route(self, resource, resource_id, http_method, method_name, params=None, data=None,
                           return_json=True, send_json=True, content_type=None):
        resource = resource.strip("/")
        params = self._encode_dict(params)
        url_fields = (self.base_endpoint_url, resource, resource_id, method_name)
        async with getattr(self.session, http_method.lower())(
                "/".join((field for field in url_fields if field is not None)) + '/',
                params=params,
                json=data if send_json else None,
                data=None if send_json else data,
                headers={} if content_type is None else {'content-type': content_type}
        ) as rep:
            if rep.status == 204:
                return

            if return_json:
                return await self.rep_to_json(rep)
            await self.check_rep(rep)
            return await rep.read()

    async def list_route(self, resource, http_method, method_name, params=None, data=None, return_json=True,
                         send_json=True):
        resource = resource.strip("/")
        params = self._encode_dict(params)
        async with getattr(
                self.session,
                http_method.lower())(
                    "%s/%s/%s/" % (self.base_endpoint_url, resource, method_name),
                    params=params,
                    json=data if send_json else None,
                    data=None if send_json else data
        ) as rep:
            if rep.status == 204:
                return

            if return_json:
                return await self.rep_to_json(rep)
            await self.check_rep(rep)
            return await rep.read()

    async def destroy(self, resource, resource_id, params=None):
        resource = resource.strip("/")
        params = self._encode_dict(params)
        async with self.session.delete(
                        "%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id), params=params) as rep:
            if rep.status == 204:
                return
            return await self.rep_to_json(rep)

    async def _check_is_on_request(self):
        if self._is_on_request is None:
            raise NotImplementedError
        async with self.session.get(self.base_endpoint_url + "/" + self._is_on_request.strip("/") + "/") as rep:
            if rep.status == 503:
                raise TimeoutError

    @staticmethod
    def _encode_dict(params):
        # make the dict readable by asyncio
        enc_params = MultiDict()
        if params is not None:
            for key, val in params.items():
                if val is None:
                    continue
                try:
                    enc_params.add(key, val.strftime(ISO_FORMAT))
                except AttributeError:
                    enc_params.add(key, json_dumps(val).strip('"'))  # we use json_dumps for uuids
        return enc_params

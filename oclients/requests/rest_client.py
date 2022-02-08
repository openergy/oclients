from .base import RequestsClient

from ..snippets.ojson import dumps as json_dumps
from ..snippets.odatetime import ISO_FORMAT

JSON_HEADER = {"content-type": "application/json"}


class RESTClient(RequestsClient):
    def __init__(
            self,
            host,
            port,
            credentials=None,
            timeout=None,
            root_endpoint="",
            is_on_resource="/",
            verify_ssl=True
    ):
        """
        is_on_resource: put None if you don't want to use it
        """
        super().__init__(host, port, credentials=credentials, timeout=timeout)
        self.base_endpoint_url = self.base_url + "/" + root_endpoint.strip("/")
        self._is_on_request = is_on_resource
        self.verify_ssl = verify_ssl

    def list(self, resource, params=None):
        resource = resource.strip("/")
        rep = self.session.get(
            "%s/%s/" % (self.base_endpoint_url, resource),
            params=self._encode_dict(params),
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        return self.rep_to_json(rep)

    def list_iter_all(self, resource, params=None):
        start = 0
        if params is None:
            params = {}
        while True:
            params["start"] = start
            current = self.list(resource, params=params)
            data = current["data"]
            if len(data) == 0:  # todo: should not need to perform last request
                break
            start += len(data)
            for element in data:
                yield element

    def retrieve(self, resource, resource_id):
        resource = resource.strip("/")
        rep = self.session.get(
            "%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id),
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        return self.rep_to_json(rep)

    def create(self, resource, data):
        resource = resource.strip("/")
        rep = self.session.post(
            "%s/%s/" % (self.base_endpoint_url, resource),
            data=json_dumps(data).encode("utf-8"),
            verify=self.verify_ssl,
            headers=JSON_HEADER,
            timeout=self.timeout
        )
        return self.rep_to_json(rep)

    def partial_update(self, resource, resource_id, data):
        resource = resource.strip("/")
        rep = self.session.patch(
            "%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id),
            data=json_dumps(data).encode("utf-8"),
            verify=self.verify_ssl,
            headers=JSON_HEADER,
            timeout=self.timeout
        )
        return self.rep_to_json(rep)

    def update(
            self,
            resource,
            resource_id,
            data):
        resource = resource.strip("/")
        rep = self.session.put(
            "%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id),
            data=json_dumps(data).encode("utf-8"),
            verify=self.verify_ssl,
            headers=JSON_HEADER,
            timeout=self.timeout
        )
        return self.rep_to_json(rep)

    def detail_route(
            self,
            resource,
            resource_id,
            http_method,
            method_name,
            params=None,
            data=None,
            return_json=True,
            send_json=True,
            content_type=None):
        resource = resource.strip("/")
        # prepare headers
        if content_type is None:
            headers = JSON_HEADER if send_json else {}
        else:
            headers = {"content-type": content_type}

        # send request
        url_fields = (self.base_endpoint_url, resource, resource_id, method_name)
        rep = getattr(self.session, http_method.lower())(
            "/".join((field for field in url_fields if field is not None)) + "/",
            params=self._encode_dict(params),
            data=json_dumps(data).encode("utf-8") if send_json and data is not None else data,
            verify=self.verify_ssl,
            headers=headers,
            timeout=self.timeout
        )
        if rep.status_code == 204:
            return

        if return_json:
            return self.rep_to_json(rep)
        self.check_rep(rep)
        return rep.content

    def list_route(
            self,
            resource,
            http_method,
            method_name,
            params=None,
            data=None,
            return_json=True,
            send_json=True):
        resource = resource.strip("/")
        rep = getattr(self.session, http_method.lower())(
            "%s/%s/%s/" % (self.base_endpoint_url, resource, method_name),
            params=self._encode_dict(params),
            data=json_dumps(data).encode("utf-8") if send_json and data is not None else data,
            verify=self.verify_ssl,
            headers=JSON_HEADER if send_json else None,
            timeout=self.timeout
        )
        if rep.status_code == 204:
            return

        if return_json:
            return self.rep_to_json(rep)
        self.check_rep(rep)
        return rep.content

    def destroy(self, resource, resource_id, params=None):
        resource = resource.strip("/")
        rep = self.session.delete(
            "%s/%s/%s/" % (self.base_endpoint_url, resource, resource_id),
            params=self._encode_dict(params),
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        if rep.status_code == 204:
            return
        return self.rep_to_json(rep)

    def _check_is_on_request(self):
        if self._is_on_request is None:
            raise NotImplementedError
        rep = self.session.get(
            self.base_endpoint_url + "/" + self._is_on_request.strip("/") + "/",
            verify=self.verify_ssl,
            timeout=self.timeout
        )
        if rep.status_code == 503:
            raise TimeoutError

    @staticmethod
    def _encode_dict(params):
        # make the dict readable by requests
        enc_params = dict()
        if params is not None:
            for key, val in params.items():
                if val is None:
                    continue
                if key not in enc_params:
                    enc_params[key] = list()
                try:
                    enc_params[key].append(val.strftime(ISO_FORMAT))
                except AttributeError:
                    enc_params[key].append(json_dumps(val).strip('"'))  # we use json_dumps for uuids
        return enc_params

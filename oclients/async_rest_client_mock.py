import uuid

from .exceptions import ClientResponseError


class AsyncRESTClientMock:
    custom_pks = None

    def __init__(self, host, port, credentials=None, root_endpoint="", is_on_resource="/"):
        """
        is_on_resource: put None if you don't want to use it
        """
        self._resources = {}  # {resource_name: {resource_pk: ...
        self.custom_pks = {} if self.custom_pks is None else self.custom_pks

    async def _check_exists(self, resource):
        if resource not in self._resources:
            self._resources[resource] = {}

    def _get_pk(self, resource):
        return self.custom_pks[resource] if (resource in self.custom_pks) else "id"

    def reset(self):
        self._resources = {}

    async def list(self, resource, params=None):
        resource = resource.strip("/")
        await self._check_exists(resource)
        return list(self._resources[resource].values())

    async def retrieve(self, resource, resource_pk):
        resource = resource.strip("/")
        await self._check_exists(resource)
        if resource_pk not in self._resources[resource]:
            raise ClientResponseError(code=404)
        return self._resources[resource][resource_pk]

    async def create(self, resource, data):
        resource = resource.strip("/")
        await self._check_exists(resource)

        pk_key = self._get_pk(resource)
        if pk_key in data:
            resource_pk = data[pk_key]
        else:
            resource_pk = uuid.uuid4()
            data[pk_key] = resource_pk
        self._resources[resource][resource_pk] = data
        return data

    async def partial_update(self, resource, resource_pk, data):
        resource = resource.strip("/")
        await self._check_exists(resource)
        stored_resource = self.retrieve(resource, resource_pk)
        for k, v in data.items():
            stored_resource[k] = v
        return resource

    async def detail_route(
            self,
            resource,
            resource_pk,
            http_method,
            method_name,
            params=None,
            data=None,
            return_json=True):
        return {}

    async def destroy(self, resource, resource_pk):
        resource = resource.strip("/")
        # check exists
        await self.retrieve(resource, resource_pk)
        # delete
        del self._resources[resource][resource_pk]

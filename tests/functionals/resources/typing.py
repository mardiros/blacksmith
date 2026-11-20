from blacksmith import AsyncClientProtocol, HTTPError
from tests.functionals.resources.api.items import ItemRoutes
from tests.functionals.resources.api.upload import UploadComplexRoutes, UploadRoutes
from tests.functionals.resources.extra.dummies import DummiesRoutes


class APIClient(AsyncClientProtocol[HTTPError]):
    item: ItemRoutes
    upload: UploadRoutes
    upload_complex: UploadComplexRoutes


class ExtraClient(AsyncClientProtocol[HTTPError]):
    dummies: DummiesRoutes

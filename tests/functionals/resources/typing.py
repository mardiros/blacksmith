from blacksmith import AsyncClientBase, HTTPError
from tests.functionals.resources.api.items import ItemRoutes
from tests.functionals.resources.api.upload import UploadComplexRoutes, UploadRoutes
from tests.functionals.resources.extra.dummies import DummiesRoutes


class APIClient(AsyncClientBase[HTTPError]):
    item: ItemRoutes
    upload: UploadRoutes
    upload_complex: UploadComplexRoutes


class ExtraClient(AsyncClientBase[HTTPError]):
    dummies: DummiesRoutes

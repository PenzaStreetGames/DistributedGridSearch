import pydantic
from typing import Optional

import src.common.models.web as common_web
import src.data_controller.models.core as core

MAGNET_LINK_REGEX = r'urn:btih:([A-F\d]+)'


class Dataset(pydantic.BaseModel):
    dataset_uid: pydantic.UUID4
    magnet_link: Optional[str] = pydantic.Field(pattern=MAGNET_LINK_REGEX)
    path: pydantic.DirectoryPath
    status: core.DatasetStatus

    @staticmethod
    def from_core(obj: core.Dataset) -> 'Dataset':
        return Dataset(
            dataset_uid=obj.dataset_uid,
            magnet_link=obj.magnet_link,
            path=obj.path,
            status=obj.status,
        )

    def to_core(self) -> core.Dataset:
        return core.Dataset(
            dataset_uid=self.dataset_uid,
            magnet_link=self.magnet_link,
            path=self.path,
            status=self.status,
        )


class DataPublishRequest(pydantic.BaseModel):
    path: pydantic.FilePath


class DataPublishResponse(common_web.BaseResponse):
    dataset_uid: pydantic.UUID4


class DataDownloadRequest(pydantic.BaseModel):
    dataset_uid: pydantic.UUID4
    magnet_link: str = pydantic.Field(pattern=MAGNET_LINK_REGEX)


class DataDownloadResponse(common_web.BaseResponse):
    dataset_uid: pydantic.UUID4


class GetDataRequest(pydantic.BaseModel):
    dataset_uid: pydantic.UUID4

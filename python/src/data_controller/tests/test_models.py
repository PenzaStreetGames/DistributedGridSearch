import pathlib
from typing import Optional
import uuid

import pytest

import src.data_controller.models.core as core
import src.data_controller.models.db as db
import src.data_controller.models.web as web

CONST_DATASET_UUID = 'ebe2ed89-0470-4e3f-b6a8-75614774f853'
CONST_MAGNET_LINK = (
    'magnet:?xt=urn:btih:9b3544af24b9ec2d7591b9f7934b1ad9ee7df88f'
)


@pytest.mark.parametrize(
    'dataset_status, magnet_link',
    [
        pytest.param(
            core.DatasetStatus.CREATING, None,
        ),
        pytest.param(
            core.DatasetStatus.DOWNLOADING, CONST_MAGNET_LINK,
        ),
        pytest.param(
            core.DatasetStatus.PUBLISHING, CONST_MAGNET_LINK,
        ),
        pytest.param(
            core.DatasetStatus.AVAILABLE, CONST_MAGNET_LINK,
        )
    ]
)
def test_dataset_model_core_db_web_conversion(
    dataset_status: core.DatasetStatus, magnet_link: Optional[str],
):
    path = pathlib.Path(__file__).parent
    core_model = core.Dataset(
        dataset_uid=uuid.UUID(CONST_DATASET_UUID),
        magnet_link=magnet_link,
        path=path,
        status=dataset_status,
    )
    db_model = db.Dataset(
        dataset_uid=CONST_DATASET_UUID,
        magnet_link=magnet_link,
        path=str(path),
        status=dataset_status.value,
    )
    web_model = web.Dataset(
        dataset_uid=uuid.UUID(CONST_DATASET_UUID),
        magnet_link=magnet_link,
        path=path,
        status=dataset_status,
    )
    mapped_db_model = db.Dataset.from_core(core_model)
    assert mapped_db_model.dataset_uid == db_model.dataset_uid
    assert mapped_db_model.magnet_link == db_model.magnet_link
    assert mapped_db_model.path == db_model.path
    assert mapped_db_model.status == db_model.status
    mapped_core_model = mapped_db_model.to_core()
    assert mapped_core_model == core_model
    mapped_web_model = web.Dataset.from_core(core_model)
    assert mapped_web_model == web_model
    mapped_core_model = mapped_web_model.to_core()
    assert mapped_core_model == core_model

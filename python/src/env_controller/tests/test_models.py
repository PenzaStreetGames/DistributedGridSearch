import pytest
from typing import Optional
import uuid

import src.env_controller.models.core as core
import src.env_controller.models.db as db
import src.env_controller.models.web as web

CONST_IMAGE_TAG = 'repo/tag:checksum'
CONST_IMAGE_ID = (
    'a6bd8ef623d388885e18b203f1e7dd4c5b55f668fe522c263396160b3492f730'
)
CONST_CONTAINER_ID = (
    'ad1561329500c6a972db965433d09544b32e237425822d2d8faa62d47b98dad8'
)
CONST_SUBTASK_UUID = '525ca440-4673-46ba-8d04-4c9cf5e29bb2'


@pytest.mark.parametrize(
    'status, image_id',
    [
        pytest.param(core.ImageStatus.CREATING, None),
        pytest.param(core.ImageStatus.BUILDING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.BUILDING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHED, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLED, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.ARCHIVED, CONST_IMAGE_ID),
    ]
)
def test_image_model_core_db_conversion(
    status: core.ImageStatus, image_id: Optional[str],
):
    core_model = core.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=image_id,
        status=status,
    )
    db_model = db.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=image_id,
        status=status.value,
    )
    db_mapped_model = db.Image.from_core(core_model)
    assert db_mapped_model.image_tag == db_model.image_tag
    assert db_mapped_model.image_id == db_model.image_id
    assert db_mapped_model.status == db_model.status
    core_mapped_model = db_mapped_model.to_core()
    assert core_mapped_model == core_model


@pytest.mark.parametrize(
    'image_status, subtask_status, container_id',
    [
        pytest.param(
            core.ImageStatus.CREATING, core.SubtaskStatus.CREATING, None,
        ),
        pytest.param(
            core.ImageStatus.BUILDING,
            core.SubtaskStatus.RUNNING,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.BUILDING_ERROR,
            core.SubtaskStatus.SUCCESS,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHING,
            core.SubtaskStatus.ERROR,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHING_ERROR,
            core.SubtaskStatus.TIMEOUT,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHED,
            core.SubtaskStatus.CANCELLED,
            CONST_CONTAINER_ID,
        ),
    ],
)
def test_subtask_model_core_db_conversion(
    image_status: core.ImageStatus,
    subtask_status: core.SubtaskStatus,
    container_id: Optional[str],
):
    core_image_model = core.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=CONST_IMAGE_ID,
        status=image_status,
    )
    db_image_model = db.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=CONST_IMAGE_ID,
        status=image_status.value,
    )
    core_model = core.Subtask(
        subtask_uid=uuid.UUID(CONST_SUBTASK_UUID),
        image=core_image_model,
        container_id=container_id,
        status=subtask_status,
    )
    db_model = db.Subtask(
        subtask_uid=CONST_SUBTASK_UUID,
        image_tag=CONST_IMAGE_TAG,
        container_id=container_id,
        status=subtask_status.value,
    )
    mapped_db_model = db.Subtask.from_core(core_model)
    assert mapped_db_model.subtask_uid == db_model.subtask_uid
    assert mapped_db_model.image_tag == db_model.image_tag
    assert mapped_db_model.container_id == db_model.container_id
    assert mapped_db_model.status == db_model.status
    mapped_db_model.image = db_image_model
    mapped_core_model = mapped_db_model.to_core()
    assert mapped_core_model == core_model


@pytest.mark.parametrize(
    'status, image_id',
    [
        pytest.param(core.ImageStatus.CREATING, None),
        pytest.param(core.ImageStatus.BUILDING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.BUILDING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PUSHED, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLING, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLING_ERROR, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.PULLED, CONST_IMAGE_ID),
        pytest.param(core.ImageStatus.ARCHIVED, CONST_IMAGE_ID),
    ]
)
def test_image_model_core_web_conversion(
    status: core.ImageStatus, image_id: Optional[str]
):
    core_model = core.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=image_id,
        status=status,
    )
    web_model = web.Image(
        image_tag=CONST_IMAGE_TAG,
        image_id=image_id,
        status=status,
    )
    mapped_web_model = web.Image.from_core(core_model)
    assert mapped_web_model == web_model
    mapped_core_model = mapped_web_model.to_core()
    assert mapped_core_model == core_model


@pytest.mark.parametrize(
    'image_status, subtask_status, container_id',
    [
        pytest.param(
            core.ImageStatus.CREATING, core.SubtaskStatus.CREATING, None,
        ),
        pytest.param(
            core.ImageStatus.BUILDING,
            core.SubtaskStatus.RUNNING,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.BUILDING_ERROR,
            core.SubtaskStatus.SUCCESS,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHING,
            core.SubtaskStatus.ERROR,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHING_ERROR,
            core.SubtaskStatus.TIMEOUT,
            CONST_CONTAINER_ID,
        ),
        pytest.param(
            core.ImageStatus.PUSHED,
            core.SubtaskStatus.CANCELLED,
            CONST_CONTAINER_ID,
        ),
    ],
)
def test_subtask_model_core_web_conversion(
    image_status: core.ImageStatus,
    subtask_status: core.SubtaskStatus,
    container_id: Optional[str],
):
    core_model = core.Subtask(
        subtask_uid=uuid.UUID(CONST_SUBTASK_UUID),
        image=core.Image(
            image_tag=CONST_IMAGE_TAG,
            image_id=CONST_IMAGE_ID,
            status=image_status,
        ),
        container_id=container_id,
        status=subtask_status,
    )
    web_model = web.Subtask(
        subtask_uid=uuid.UUID(CONST_SUBTASK_UUID),
        image=web.Image(
            image_tag=CONST_IMAGE_TAG,
            image_id=CONST_IMAGE_ID,
            status=image_status,
        ),
        container_id=container_id,
        status=subtask_status,
    )
    mapped_web_model = web.Subtask.from_core(core_model)
    assert mapped_web_model == web_model
    mapped_core_model = mapped_web_model.to_core()
    assert mapped_core_model == core_model

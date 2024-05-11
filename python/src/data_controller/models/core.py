import dataclasses
import enum
import pathlib
from typing import Optional
import uuid


class DatasetStatus(enum.Enum):
    CREATING = 'creating'
    PUBLISHING = 'publishing'
    DOWNLOADING = 'downloading'
    AVAILABLE = 'available'


@dataclasses.dataclass
class Dataset:
    dataset_uid: uuid.UUID
    magnet_link: Optional[str]
    path: pathlib.Path
    status: DatasetStatus

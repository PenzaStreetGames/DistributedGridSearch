import pathlib
import shutil
import threading
import time
from typing import Optional
import uuid

import torrentool.api
import qbittorrent

import src.data_controller.backend.repositories as repositories
import src.data_controller.models.core as models

DEFAULT_TORRENT_WEB_UI_PORT = 8090
PUBLISHING_POLLING_TIMEOUT = 10
DOWNLOADING_POLLING_TIMEOUT = 120


class TorrentService:
    def __init__(self, dataset_repository: repositories.DatasetRepository):
        self.dataset_repository = dataset_repository
        self.client = qbittorrent.Client(
            f'http://127.0.0.1:{DEFAULT_TORRENT_WEB_UI_PORT}'
        )

    def publish_dataset(self, dataset_path: pathlib.Path) -> models.Dataset:
        dataset_uid = uuid.uuid4()
        print(f'copying dataset {dataset_uid} files to storage')
        dataset_storage_path = self.dataset_storage / str(dataset_uid)
        dataset = models.Dataset(
            dataset_uid=dataset_uid,
            magnet_link=None,
            path=dataset_storage_path,
            status=models.DatasetStatus.CREATING,
        )
        self.dataset_repository.create_entity(dataset)
        thread = threading.Thread(
            target=self._publish_dataset,
            args=(dataset_uid, dataset_path, dataset_storage_path),
        )
        thread.start()
        return dataset

    def download_dataset(
        self, dataset_uid: uuid.UUID, magnet_link: str,
    ) -> models.Dataset:
        dataset_storage_path = self.dataset_storage / str(dataset_uid)
        dataset = models.Dataset(
            dataset_uid=dataset_uid,
            magnet_link=magnet_link,
            path=dataset_storage_path,
            status=models.DatasetStatus.DOWNLOADING,
        )
        self.dataset_repository.create_entity(dataset)
        thread = threading.Thread(
            target=self._download_dataset, args=(dataset,),
        )
        thread.start()
        return dataset

    def _publish_dataset(
        self,
        dataset_uid: uuid.UUID,
        dataset_path: pathlib.Path,
        dataset_storage_path: pathlib.Path
    ):
        dataset = self.dataset_repository.get_entity(dataset_uid)
        self._copy_to_storage(dataset_path, dataset_storage_path)
        print(f'dataset {dataset_uid} files has been copied to storage')
        torrent_file_path = (
            self.torrent_files_storage / f'{dataset_uid}.torrent'
        )
        print(f'making torrent file {torrent_file_path.name}')
        torrent_file = self.make_torrent_file(
            torrent_file_path, dataset_storage_path,
        )
        print(f'torrent file {torrent_file.name} has been made')
        dataset.status = models.DatasetStatus.PUBLISHING
        self.dataset_repository.update_entity(dataset)
        print(f'publishing dataset {dataset_uid} via local qbittorent client')
        self.client.download_from_file(
            torrent_file_path.read_bytes(),
            save_path=dataset_storage_path.parent,
        )
        print(
            f'dataset {dataset_uid} has been published '
            'via local qbittorent client',
        )
        self._wait_dataset(dataset_uid)
        dataset.magnet_link = torrent_file.magnet_link
        dataset.status = models.DatasetStatus.AVAILABLE
        self.dataset_repository.update_entity(dataset)

    def _download_dataset(self, dataset: models.Dataset):
        self.client.download_from_link(
            dataset.magnet_link, savepath=dataset.path,
        )
        self._wait_dataset(
            dataset.dataset_uid, timeout=DOWNLOADING_POLLING_TIMEOUT,
        )
        dataset.status = models.DatasetStatus.AVAILABLE
        self.dataset_repository.update_entity(dataset)

    def _wait_dataset(
        self,
        dataset_uid: uuid.UUID,
        timeout: float = PUBLISHING_POLLING_TIMEOUT,
    ):
        start = time.time()
        progress = self._get_dataset_progress(dataset_uid)
        while progress < 1:
            time.sleep(0.1)
            progress = self._get_dataset_progress(dataset_uid)
            if time.time() - start > timeout:
                raise TimeoutError(f'Could not publish dataset {dataset_uid}')

    def _get_dataset(self, dataset_uid: uuid.UUID) -> Optional[dict]:
        for torrent in self.client.torrents():
            if torrent['name'] == str(dataset_uid):
                return torrent
        return None

    def _get_dataset_progress(self, dataset_uid: uuid.UUID) -> int | float:
        dataset = self._get_dataset(dataset_uid)
        if dataset is None:
            return 0
        return dataset['progress']

    def _copy_to_storage(
        self, dataset_path: pathlib.Path, dataset_storage_path: pathlib.Path,
    ) -> None:
        if dataset_path.is_file():
            dst_path = dataset_storage_path / dataset_path.name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(dataset_path, dst_path)
        for src_path in dataset_path.rglob('*'):
            if not src_path.is_file():
                continue
            dst_path = (
                dataset_storage_path / src_path.relative_to(dataset_path)
            )
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dst_path)

    @staticmethod
    def make_torrent_file(
        torrent_file: pathlib.Path, dataset_storage_path: pathlib.Path,
    ) -> torrentool.api.Torrent:
        new_torrent = torrentool.api.Torrent.create_from(dataset_storage_path)
        new_torrent.to_file(str(torrent_file))
        return new_torrent

    @property
    def torrent_files_storage(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'torrents'

    @property
    def dataset_storage(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'datasets'


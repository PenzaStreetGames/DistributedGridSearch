import pathlib
import uuid

import src.data_controller.backend.repositories as repositories
import src.data_controller.backend.torrent_service as torrent
import src.data_controller.models.core as models


class DatasetService:
    def __init__(
        self,
        dataset_repository: repositories.DatasetRepository,
        torrent_service: torrent.TorrentService,
    ):
        self.dataset_repository = dataset_repository
        self.torrent_service = torrent_service

    def publish_dataset(self, dataset_path: pathlib.Path) -> models.Dataset:
        dataset = self.torrent_service.publish_dataset(dataset_path)
        return dataset

    def download_dataset(
        self, dataset_uid: uuid.UUID, magnet_link: str,
    ) -> models.Dataset:
        dataset = self.torrent_service.download_dataset(
            dataset_uid, magnet_link,
        )
        return dataset

    def get_dataset(
        self, dataset_uid: uuid.UUID,
    ) -> models.Dataset:
        return self.dataset_repository.get_entity(dataset_uid)

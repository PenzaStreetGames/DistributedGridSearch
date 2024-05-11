import json
import pathlib
import shutil
from typing import Any
import uuid

import checksumdir

import src.env_controller.backend.repositories as repositories
import src.env_controller.backend.docker_service as docker
import src.env_controller.models.core as models


class ImageService:
    def __init__(
        self,
        repository: repositories.ImageRepository,
        docker_service: docker.DockerService,
    ):
        self.repository = repository
        self.docker_service = docker_service

    def build_and_push(
        self,
        task_type: models.TaskType,
        subtask_type: models.SubtaskType,
    ) -> models.Image:
        task_folder = self._tasks_repo / task_type.value.lower()
        subtask_folder = task_folder / 'subtasks' / subtask_type.value.lower()
        assert subtask_folder.exists(), (
            f'subtask folder {subtask_folder} does not exist'
        )
        subtask_name = subtask_type.value.lower()
        subtask_checksum = checksumdir.dirhash(subtask_folder, hashfunc='md5')
        tag = f'distcalcanonymous/{subtask_name}:{subtask_checksum}'
        image = self.docker_service.build_and_push_image(subtask_folder, tag)
        return image

    def pull_image(self, image_tag: str) -> models.Image:
        image = self.docker_service.pull_image(image_tag)
        return image

    def get_image_status(self, image_tag: str) -> models.ImageStatus:
        image = self.repository.get_entity(image_tag=image_tag)
        return image.status

    @property
    def _tasks_repo(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'tasks'


class SubtaskService:
    def __init__(
        self,
        subtask_repository: repositories.SubtaskRepository,
        image_repository: repositories.ImageRepository,
        docker_service: docker.DockerService,
    ):
        self.subtask_repository = subtask_repository
        self.image_repository = image_repository
        self.docker_service = docker_service

    def run_container(
        self,
        subtask_uid: uuid.UUID,
        image_tag: str,
        input_files: list[pathlib.Path],
    ) -> models.Subtask:
        image = self.image_repository.get_entity(image_tag)
        subtask = models.Subtask(
            subtask_uid=subtask_uid,
            image=image,
            container_id=None,
            status=models.SubtaskStatus.CREATING
        )
        self.subtask_repository.create_entity(subtask)
        subtask_runtime_dir = self.get_subtask_runtime_dir(subtask.subtask_uid)
        subtask.status = models.SubtaskStatus.FILE_COPYING
        self.subtask_repository.update_entity(subtask)
        self._copy_input_files(
            input_files=input_files, subtask_runtime_dir=subtask_runtime_dir,
        )
        subtask = self.docker_service.run_container(
            subtask,
            input_path=subtask_runtime_dir / 'input',
            output_path=subtask_runtime_dir / 'output',
        )
        return subtask

    def _copy_input_files(
        self,
        input_files: list[pathlib.Path],
        subtask_runtime_dir: pathlib.Path,
    ):
        print('copying input files')
        for src_path in input_files:
            dst_path = subtask_runtime_dir / 'input' / src_path.name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dst_path)
        print('input files has been copied')

    def get_container_status(
        self, subtask_uid: uuid.UUID,
    ) -> models.SubtaskStatus:
        subtask = self.subtask_repository.get_entity(subtask_uid)
        return subtask.status

    def get_subtask_result(
        self, subtask_uid: uuid.UUID,
    ) -> pathlib.Path:
        subtask_runtime_dir = self.get_subtask_runtime_dir(subtask_uid)
        result_file = subtask_runtime_dir / 'output' / 'result.json'
        assert result_file.exists(), (
            f'result of subtask {subtask_uid} not ready'
        )
        return result_file

    @property
    def runtime_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent.parent / 'runtime'

    def get_subtask_runtime_dir(self, subtask_uid: uuid.UUID) -> pathlib.Path:
        return self.runtime_dir / str(subtask_uid)

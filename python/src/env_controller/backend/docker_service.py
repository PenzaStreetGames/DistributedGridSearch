import pathlib
import threading

import checksumdir
import docker

import src.env_controller.backend.repositories as repositories
import src.env_controller.models.core as models


DOCKER_USER = 'distcalcanonymous'
DOCKER_PASSWORD = 'dckr_pat_DVvkJ0bp-mg5j8v6uf_YpARZI74'


class DockerService:
    def __init__(
        self,
        image_repository: repositories.ImageRepository,
        subtask_repository: repositories.SubtaskRepository,
    ):
        self.image_repository = image_repository
        self.subtask_repository = subtask_repository
        self.client = docker.from_env()
        self.client.login(username=DOCKER_USER, password=DOCKER_PASSWORD)

    def build_and_push_image(
        self, subtask_folder: pathlib.Path, tag: str,
    ) -> models.Image:

        image = models.Image(
            image_tag=tag,
            image_id=None,
            status=models.ImageStatus.BUILDING,
        )
        self.image_repository.upsert_entity(image)
        thread = threading.Thread(
            target=self._build_and_push_image, args=(subtask_folder, tag),
        )
        thread.start()
        return image

    def _build_and_push_image(self, path: pathlib.Path, tag: str):
        print(f'building image {tag}...')
        image = self.image_repository.get_entity(image_tag=tag)

        docker_image, logs = self.client.images.build(path=str(path), tag=tag)

        image.image_id = docker_image.id
        self.image_repository.update_entity(image)
        print(f'image {tag} has been built')

        print(f'pushing image {tag} to dockerhub')
        image.status = models.ImageStatus.PUSHING
        self.image_repository.update_entity(image)

        self.client.images.push(repository=tag)

        image.status = models.ImageStatus.PUSHED
        self.image_repository.update_entity(image)
        print(f'image {tag} has been pushed to dockerhub')

    def pull_image(self, tag: str) -> models.Image:
        image = models.Image(
            image_tag=tag,
            image_id=None,
            status=models.ImageStatus.PULLING,
        )
        self.image_repository.upsert_entity(image)
        thread = threading.Thread(target=self._pull_image, args=(tag,))
        thread.start()
        return image

    def _pull_image(self, tag: str):
        print(f'pulling image {tag} from dockerhub')
        image = self.image_repository.get_entity(image_tag=tag)

        docker_image = self.client.images.pull(repository=tag)

        image.image_id = docker_image.id
        image.status = models.ImageStatus.PULLED
        self.image_repository.update_entity(image)
        print(f'image {tag} has been pulled from dockerhub')

    def run_container(
        self,
        subtask: models.Subtask,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ) -> models.Subtask:
        subtask.status = models.SubtaskStatus.RUNNING
        self.subtask_repository.update_entity(subtask)
        thread = threading.Thread(
            target=self._run_container,
            args=(subtask, input_path, output_path),
        )
        thread.start()
        return subtask

    def _run_container(
        self,
        subtask: models.Subtask,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ):
        tag = subtask.image.image_tag
        params = f'tag: {tag}, input {input_path}, output: {output_path}'
        print(f'running container {params}')
        self.client.containers.run(
            image=tag,
            volumes={
                str(input_path): {'bind': '/usr/src/app/input', 'mode': 'ro'},
                str(output_path): {
                    'bind': '/usr/src/app/output', 'mode': 'rw',
                },
            },
        )
        print(f'container {params} has been finished')
        subtask.status = models.SubtaskStatus.SUCCESS
        self.subtask_repository.update_entity(subtask)

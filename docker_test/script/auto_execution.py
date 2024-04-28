import pathlib

import checksumdir
import docker
import yaml


def extract_subtask_name(task_path: pathlib.Path) -> str:
    data = yaml.safe_load(task_path.read_text())
    return data['subtask']['name']


def build_image(client: docker.DockerClient, task_path: pathlib.Path) -> str:
    subtask_name = extract_subtask_name(task_path / 'subtask.yaml').lower()
    subtask_checksum = checksumdir.dirhash(task_path, hashfunc='md5')
    tag = f'{subtask_name}:{subtask_checksum}'
    print(f'building image {tag}...')
    client.images.build(
        path=str(task_path.parent),
        tag=tag,
    )
    print(f'image {tag} has been built')
    return tag


def run_container(
    client: docker.DockerClient,
    tag: str,
    input_path: pathlib.Path,
    output_path: pathlib.Path,
) -> None:
    params = f'{{tag: {tag}, input {input_path}, output: {output_path}}}',
    print(f'running container {params}')
    client.containers.run(
        image=tag,
        volumes={
            str(input_path): {'bind': '/usr/src/app/input', 'mode': 'ro'},
            str(output_path): {'bind': '/usr/src/app/output', 'mode': 'rw'},
        },
    )
    print(f'container {params} has been finished')


def push_image(client: docker.DockerClient, tag: str) -> str:
    image = client.images.get(tag)
    tag_for_push = f'penzastreet/{tag}'
    image.tag(f'penzastreet/{tag}')
    print(f'pushing image {tag_for_push} to dockerhub')
    client.images.push(repository=tag_for_push)
    print(f'image {tag_for_push} has been pushed to dockerhub')
    return tag_for_push


def pull_image(client: docker.DockerClient, tag: str) -> None:
    print(f'pulling image {tag} from dockerhub')
    client.images.pull(repository=tag)
    print(f'image {tag} has been pulled from dockerhub')


def main():
    client = docker.from_env()
    task_path = pathlib.Path('../tasks_collection/task/subtask').resolve()
    runtime_path = pathlib.Path('../runtime/subtask_id').resolve()
    input_path = runtime_path / 'input'
    output_path = runtime_path / 'output'
    tag = build_image(client, task_path)
    tag_for_push = push_image(client, tag)
    pull_image(client, tag_for_push)
    run_container(client, tag_for_push, input_path, output_path)


if __name__ == '__main__':
    main()

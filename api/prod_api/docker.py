import docker
from docker.models.containers import Container


def client() -> docker.DockerClient:
    """
    Returns the Docker client.
    """

    return docker.from_env()


def docker_health() -> dict:
    """
    Returns Docker health.
    """

    try:
        client().ping()

        return {
            "provider": "docker",
            "healthy": True,
        }

    except Exception as e:

        return {
            "provider": "docker",
            "healthy": False,
            "error": str(e),
        }


def image_name(container: Container) -> str:
    """
    Returns the container image name.
    """

    image = container.image

    if image is None:
        return "<none>"

    if not image.tags:
        return "<none>"

    return image.tags[0]


def containers() -> dict:
    """
    Returns all Docker containers.
    """

    docker_client = client()
    all_containers = docker_client.containers.list(all=True)

    return {
        "containers": [
            {
                "id": container.short_id,
                "name": container.name,
                "image": image_name(container),
                "status": container.status,
            }
            for container in all_containers
        ]
    }


def container(name: str) -> dict:
    """
    Returns information about a Docker container.
    """

    c = client().containers.get(name)

    return {
        "id": c.short_id,
        "name": c.name,
        "status": c.status,
        "image": image_name(c),
    }


def restart(name: str) -> dict:
    """
    Restarts a Docker container.
    """

    c = client().containers.get(name)

    c.restart()

    return {
        "container": name,
        "status": "restarted",
    }


def logs(name: str, tail: int = 200) -> dict:
    """
    Returns Docker container logs.
    """

    c = client().containers.get(name)

    return {
        "container": name,
        "logs": c.logs(
            tail=tail,
            stdout=True,
            stderr=True,
        ).decode("utf-8"),
    }
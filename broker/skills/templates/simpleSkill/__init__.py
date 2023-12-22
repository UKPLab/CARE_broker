import docker


def create_docker(nocache=False):
    """
    Build the docker container
    :param nocache: Do not use cache
    :return:
    """
    # Create a Docker client
    client = docker.from_env()

    try:
        build_logs = client.api.build(
            dockerfile="Dockerfile",
            path="./broker/skills/templates/simpleSkill",
            tag="broker_simple_skill",
            decode=True, rm=True,
            nocache=nocache,
        )
        # Print build output in real-time
        for chunk in build_logs:
            if 'stream' in chunk:
                for line in chunk['stream'].splitlines():
                    print(line)
    except docker.errors.BuildError as e:
        print("Failed to build Docker image:", e)

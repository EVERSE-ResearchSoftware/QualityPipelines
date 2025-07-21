import subprocess


class DockerExecutor:
    """A Docker executor."""

    def __init__(self, image_url, pull_args=None):
        self.url = image_url
        if pull_args is None:
            pull_args = []
        try:
            subprocess.run(
                ["docker", "pull"] + pull_args + [self.url],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error pulling the Docker image from {self.url}: {e}")
            raise

    def run(self, command, run_args=None):
        """
        Run command (popenargs) inside a Docker container and return a
        CompletedProcess instance from the subprocess Python module.

        Extra arguments to the command can be passed as a list of
        strings via `run_args`.
        """
        if run_args is None:
            run_args = []
        cmd = ["docker", "run"] + run_args + [self.url] + command
        return subprocess.run(cmd, capture_output=True, text=True)

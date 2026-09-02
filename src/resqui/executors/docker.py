import subprocess
from resqui.executors.base import ExecutorInitError


class DockerExecutor:
    """A Docker executor."""

    def __init__(self, image_url, pull_args=None):
        self.url = image_url
        if pull_args is None:
            pull_args = []
        command = ["docker", "pull"] + pull_args + [self.url]
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            raise ExecutorInitError(
                f"failed to initialise Docker executor: '{' '.join(command)}'"
            )

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

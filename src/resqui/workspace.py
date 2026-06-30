import os
import shutil
from typing import Optional
import tempfile
from dataclasses import dataclass


SHARED_WORKDIR_ENV = "RESQUI_SHARED_WORKDIR"
DOCKER_WORK_VOLUME_ENV = "RESQUI_DOCKER_WORK_VOLUME"


@dataclass(frozen=True)
class Workspace:
    """Workspace visible to resqui and, optionally, Docker plugin containers."""

    local_path: str
    
    shared_root: Optional[str] = None
    docker_volume: Optional[str] = None

    @property
    def is_shared(self) -> bool:
        return self.shared_root is not None and self.docker_volume is not None

    def container_path(self, fallback_path: str) -> str:
        """Return the path the plugin container should use for this workspace."""
        if self.is_shared:
            return self.local_path
        return fallback_path

    def docker_mount_args(self, fallback_path: str) -> list[str]:
        """Return Docker -v arguments for exposing this workspace to a plugin."""
        if self.is_shared:
            return ["-v", f"{self.docker_volume}:{self.shared_root}"]
        return ["-v", f"{self.local_path}:{fallback_path}"]

    def cleanup(self) -> None:
        shutil.rmtree(self.local_path, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()


def create_workspace(prefix: str = "resqui-") -> Workspace:
    """Create a temporary workspace for local and Docker-backed plugin runs.

    By default, this behaves like tempfile.mkdtemp(). In worker mode, set
    RESQUI_SHARED_WORKDIR and RESQUI_DOCKER_WORK_VOLUME so plugin containers can
    mount the same Docker volume that the worker uses.
    """
    shared_root = os.getenv(SHARED_WORKDIR_ENV)
    docker_volume = os.getenv(DOCKER_WORK_VOLUME_ENV)

    if bool(shared_root) != bool(docker_volume):
        raise ValueError(
            f"{SHARED_WORKDIR_ENV} and {DOCKER_WORK_VOLUME_ENV} must be set together"
        )

    if shared_root and docker_volume:
        os.makedirs(shared_root, exist_ok=True)
        local_path = tempfile.mkdtemp(prefix=prefix, dir=shared_root)
        return Workspace(
            local_path=os.path.abspath(local_path),
            shared_root=os.path.abspath(shared_root),
            docker_volume=docker_volume,
        )

    return Workspace(local_path=tempfile.mkdtemp(prefix=prefix))

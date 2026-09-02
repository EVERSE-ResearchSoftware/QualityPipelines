import os
import tempfile
import unittest
from unittest.mock import patch

from resqui.workspace import create_workspace


class TestWorkspace(unittest.TestCase):
    def test_local_workspace_mounts_temp_dir_to_requested_container_path(self):
        with patch.dict(os.environ, {}, clear=True):
            workspace = create_workspace(prefix="test-resqui-")

        try:
            self.assertTrue(os.path.isdir(workspace.local_path))
            self.assertEqual(workspace.container_path("/path"), "/path")
            self.assertEqual(
                workspace.docker_mount_args("/path"),
                ["-v", f"{workspace.local_path}:/path"],
            )
        finally:
            workspace.cleanup()

        self.assertFalse(os.path.exists(workspace.local_path))

    def test_shared_workspace_mounts_named_volume_and_keeps_same_path(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(
                os.environ,
                {
                    "RESQUI_SHARED_WORKDIR": root,
                    "RESQUI_DOCKER_WORK_VOLUME": "sqoo_resqui_work",
                },
                clear=True,
            ):
                workspace = create_workspace(prefix="test-resqui-")

            try:
                self.assertTrue(workspace.local_path.startswith(root))
                self.assertTrue(os.path.isdir(workspace.local_path))
                self.assertEqual(workspace.container_path("/path"), workspace.local_path)
                self.assertEqual(
                    workspace.docker_mount_args("/path"),
                    ["-v", f"sqoo_resqui_work:{root}"],
                )
            finally:
                workspace.cleanup()

            self.assertFalse(os.path.exists(workspace.local_path))

    def test_partial_shared_workspace_configuration_is_rejected(self):
        with patch.dict(
            os.environ,
            {"RESQUI_SHARED_WORKDIR": "/resqui-work"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                create_workspace()

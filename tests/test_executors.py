import subprocess
import unittest
from unittest.mock import call, patch

from resqui.executors import PythonExecutor, DockerExecutor


class TestPythonExecutor(unittest.TestCase):
    def test_install_a_package_on_init(self):
        pe = PythonExecutor(packages=["ansi2txt"])
        self.assertTrue(pe.is_installed("ansi2txt"))

    def test_install_a_package_on_init_with_requirement_specifier(self):
        pe = PythonExecutor(packages=["ansi2txt==0.2.0"])
        self.assertTrue(pe.is_installed("ansi2txt", "0.2"))

    def test_install_a_package(self):
        pe = PythonExecutor()
        self.assertFalse(pe.is_installed("ansi2txt"))
        pe.install("ansi2txt==0.2.0")
        self.assertTrue(pe.is_installed("ansi2txt", "0.2"))

    def test_execute_script(self):
        pe = PythonExecutor()
        out = pe.execute("print('narf')")
        self.assertEqual(out.stdout.strip(), "narf")

    def test_execute_script_which_uses_installed_package(self):
        pe = PythonExecutor(["ansi2txt==0.2.0"])
        out = pe.execute("import ansi2txt; ansi2txt.putchar('a')")
        self.assertEqual(out.stdout.strip(), "a")


class TestDockerExecutor(unittest.TestCase):
    def test_docker_executor(self):
        with patch("resqui.executors.docker.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "installation appears to be working correctly"
            de = DockerExecutor("hello-world")
            out = de.run([])

        self.assertIn("installation appears to be working correctly", out.stdout)
        mock_run.assert_has_calls(
            [
                call(
                    ["docker", "pull", "hello-world"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
                call(["docker", "run", "hello-world"], capture_output=True, text=True),
            ]
        )

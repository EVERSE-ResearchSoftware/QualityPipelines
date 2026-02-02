import venv
import os
import tempfile
import shutil
import subprocess

from resqui.tools import normalized


class PythonExecutor:
    """A Python executor which uses a temporary virtual environment.

    The `packages` should be a list of package names with optional
    requirement specifiers as accepted by `pip`.

    More information:
    https://packaging.python.org/en/latest/glossary/#term-Requirement-Specifier

    """

    def __init__(self, packages=None, environment=None):
        """Instantiates a virtual environment in a temporary folder."""
        self.temp_dir = tempfile.mkdtemp()
        self.environment = environment if environment is not None else {}
        venv.create(self.temp_dir, with_pip=True)
        if packages is None:
            return
        for package in packages:
            self.install(package)

    def install(self, package):
        try:
            subprocess.run(
                [f"{self.temp_dir}/bin/pip", "install", package],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package} with pip: {e}")
            raise

    def is_installed(self, package_name, version=None):
        out = self.execute(
            normalized(
                """
            from importlib.metadata import distributions
            for dist in distributions():
                name = dist.metadata.get('Name', '<unknown>')
                version = getattr(dist, 'version', '<unknown>')
                print(f"{name}=={version}")
        """
            )
        )
        package = package_name + "" if version is None else f"=={version}"
        return package in out.stdout

    def execute(self, script):
        """Run the script in the virtual environment."""
        env = os.environ.copy()
        env.update(self.environment)
        return subprocess.run(
            [f"{self.temp_dir}/bin/python", "-c", script],
            capture_output=True,
            text=True,
            env=env,
        )

    def __del__(self):
        """Cleanup the temporary virtual environment on destruction."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Failed to remove virtualenv at {self.temp_dir}: {e}")

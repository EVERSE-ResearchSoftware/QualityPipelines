import unittest
from resqui.plugins import PythonExecutor


class TestPythonExecutor(unittest.TestCase):
    def test_install_a_package_on_init(self):
        pe = PythonExecutor(packages=["black"])
        assert pe.is_installed("black")

    def test_install_a_package_on_init_with_requirement_specifier(self):
        package = "black==25.1.0"
        pe = PythonExecutor(packages=[package])
        assert pe.is_installed("black", "25.1.0")

    def test_install_a_package(self):
        pe = PythonExecutor()
        assert not pe.is_installed("black")
        pe.install("black==25.1.0")
        assert pe.is_installed("black", "25.1.0")

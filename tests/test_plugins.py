import unittest
from resqui.plugins import PythonExecutor


class TestPythonExecutor(unittest.TestCase):
    def test_install_a_package_on_init(self):
        pe = PythonExecutor(packages=["ansi2txt"])
        assert pe.is_installed("ansi2txt")

    def test_install_a_package_on_init_with_requirement_specifier(self):
        package = "ansi2txt==0.2.0"
        pe = PythonExecutor(packages=[package])
        assert pe.is_installed("ansi2txt", "0.2")

    def test_install_a_package(self):
        pe = PythonExecutor()
        assert not pe.is_installed("ansi2txt")
        pe.install("ansi2txt==0.2.0")
        assert pe.is_installed("ansi2txt", "0.2")

    def test_execute_script(self):
        pe = PythonExecutor()
        out = pe.execute("print('narf')")
        assert out.stdout.strip() == "narf"

    def test_execute_script_which_uses_installed_package(self):
        pe = PythonExecutor(["ansi2txt==0.2.0"])
        out = pe.execute("import ansi2txt; ansi2txt.putchar('a')")
        print(out.stdout.strip())
        assert out.stdout.strip() == "a"

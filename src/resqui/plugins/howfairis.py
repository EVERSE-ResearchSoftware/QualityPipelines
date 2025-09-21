from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.tools import normalized


class HowFairIs(IndicatorPlugin):
    name = "HowFairIs"
    version = "0.14.2"
    python_package_name = "howfairis"
    id = "https://w3id.org/everse/tools/howfairis"
    indicators = ["has_license"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"{self.python_package_name}=={self.version}")

    def has_license(self, url, branch_hash_or_tag):
        script = normalized(
            f"""
            from howfairis import Repo, Checker
            repo = Repo("{url}", "{branch_hash_or_tag}")
            checker = Checker(repo, is_quiet=True)
            print(checker.has_license())
        """
        )
        result = self.executor.execute(script)
        output = "valid" if result.stdout.strip() == "True" else "invalid"
        if output == "valid":
            evidence = "Found license file: 'LICENSE'."
            success = True
        else:
            evidence = "No license file found."
            success = False

        return CheckResult(
            process="Searches for a file named 'LICENSE' or 'LICENSE.md' in the repository root.",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

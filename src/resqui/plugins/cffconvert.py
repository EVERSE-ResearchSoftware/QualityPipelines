from resqui.plugins.base import IndicatorPlugin
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.tools import normalized, construct_full_url


class CFFConvert(IndicatorPlugin):
    name = "CFFConvert"
    version = "2.0.0"
    python_package_name = "cffconvert"
    id = "https://w3id.org/everse/tools/cffconvert"
    indicators = ["has_citation"]

    def __init__(self, context):
        self.context = context
        self.executor = PythonExecutor()
        self.executor.install(f"{self.python_package_name}=={self.version}")

    def has_citation(self, url, branch_hash_or_tag):
        full_url = construct_full_url(url, branch_hash_or_tag)
        script = normalized(
            f"""
            from cffconvert.cli.create_citation import create_citation
            citation = create_citation(None, "{full_url}")
            if citation.validate() is None:
                print("True")
        """
        )
        result = self.executor.execute(script)

        output = "valid" if result.stdout.strip() == "True" else "invalid"
        if output == "valid":
            evidence = "Found valid CITATION.cff file in repository root."
            success = True
        else:
            evidence = "No valid CITATION.cff file found in repository root."
            success = False

        return CheckResult(
            process="Searches for a 'CITATION.cff' file in the repository root and validates its syntax.",
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

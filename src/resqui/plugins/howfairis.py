from resqui.plugins.base import IndicatorPlugin, PluginInitError
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.tools import normalized


class HowFairIs(IndicatorPlugin):
    name = "HowFairIs"
    version = "0.15.0"
    python_package_name = "howfairis"
    python_package_spec = "git+https://github.com/fair-software/howfairis.git@0.15.0"
    id = "https://w3id.org/everse/tools/howfairis"
    indicators = [
        "has_license",
        "software_has_license_for_file_types",
    ]

    def __init__(self, context):
        self.context = context
        if not context.github_token:
            raise PluginInitError("missing GITHUB_ACTION_TOKEN")
        self.executor = PythonExecutor(
            environment={"GITHUB_ACTION_TOKEN": context.github_token}
        )
        self.executor.install(self.python_package_spec)

    def has_license(self, url, branch_hash_or_tag):
        url = url.removesuffix(".git")
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

    def software_has_license_for_file_types(self, url, branch_hash_or_tag):
        url = url.removesuffix(".git")

        script = normalized(
            f"""
            try:
                from howfairis import Repo, Checker
                repo = Repo("{url}", "{branch_hash_or_tag}")
                checker = Checker(repo, is_quiet=True)
                print(checker.is_reuse_compliant())
            except Exception as exc:
                print(f"ERROR: {{exc}}")
        """
        )

        process = (
    "Checks whether the repository is compliant with the REUSE specification "
    "using HowFairIs. Reference: "
    "https://fair-impact.github.io/RSMD-guidelines/6.Reuse_legal/"
)

        result = self.executor.execute(script)
        stdout = result.stdout.strip()

        if not stdout:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=(
                    "HowFairIs did not return JSON.\n"
                    f"Return code: {getattr(result, 'returncode', 'unknown')}\n"
                    f"STDERR:\n{result.stderr.strip()}"
                ),
                success=False,
            )

        output_line = stdout.splitlines()[-1].strip()

        if output_line.startswith("ERROR:"):
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=(
                    "Could not check REUSE compliance: "
                    f"{output_line.removeprefix('ERROR:').strip()}"
                ),
                success=False,
            )

        if output_line not in {"True", "False"}:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=(
                    "Could not parse HowFairIs REUSE compliance output.\n"
                    f"STDERR:\n{result.stderr.strip()}\n"
                    f"STDOUT:\n{stdout}"
                ),
                success=False,
            )

        success = output_line == "True"
        output = "true" if success else "false"
        evidence = (
            "HowFairIs checker.is_reuse_compliant() returned "
            f"{output_line} for repository {url}."
        )

        return CheckResult(
            process=process,
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

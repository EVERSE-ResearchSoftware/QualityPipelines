import json

from resqui.plugins.base import IndicatorPlugin, PluginInitError
from resqui.executors import PythonExecutor
from resqui.core import CheckResult
from resqui.tools import normalized


class HowFairIs(IndicatorPlugin):
    name = "HowFairIs"
    version = "0.14.2"
    python_package_name = "howfairis"
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
        self.executor.install(f"{self.python_package_name}=={self.version}")

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
            import json
            from urllib.parse import urlparse

            try:
                import requests

                parsed_url = urlparse("{url}")
                reuse_url = (
                    "https://api.reuse.software/status/"
                    f"{{parsed_url.netloc}}{{parsed_url.path}}.json"
                )

                response = requests.get(reuse_url, timeout=30)
                response.raise_for_status()

                print(json.dumps(response.json()))

            except Exception as exc:
                print(json.dumps({{"error": str(exc)}}))
            """
        )

        process = (
            "Checks whether the repository is compliant with the "
            "REUSE specification using the REUSE API through HowFairIs."
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

        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=(
                    "Could not parse HowFairIs output as JSON.\n"
                    f"Error: {exc}\n"
                    f"STDERR:\n{result.stderr.strip()}\n"
                    f"STDOUT:\n{stdout}"
                ),
                success=False,
            )

        # Error while querying REUSE
        if "error" in report:
            return CheckResult(
                process=process,
                status_id="schema:FailedActionStatus",
                output="error",
                evidence=f"Could not check REUSE compliance: {report['error']}",
                success=False,
            )

        status = report.get("status", "unknown")
        lint_code = report.get("lint_code")
        lint_output = report.get("lint_output", "").strip()
        last_access = report.get("last_access")
        checked_repo = report.get("url", url)

        success = status == "compliant"
        output = "true" if success else "false"

        evidence_parts = [
            f"REUSE compliance status: {status}.",
            f"Repository checked: {checked_repo}.",
        ]

        if lint_code is not None:
            evidence_parts.append(f"REUSE lint code: {lint_code}.")

        if last_access:
            evidence_parts.append(f"REUSE last assessment: {last_access}.")

        if lint_output:
            evidence_parts.append(
                f"REUSE lint report:\n{lint_output}"
            )

        evidence = "\n".join(evidence_parts)

        return CheckResult(
            process=process,
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )

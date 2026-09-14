import json
import os

from resqui.core import CheckResult
from resqui.executors import DockerExecutor
from resqui.plugins.base import IndicatorPlugin
from resqui.workspace import create_workspace


class SOMEF(IndicatorPlugin):
    name = "SOMEF"
    id = "https://github.com/KnowledgeCaptureAndDiscovery/somef"
    version = "0.11.3"
    image_url = f"docker.io/kcapd/somef:{version}"
    indicators = ["has_active_communication_channels"]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}




    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = url.removesuffix(".git")
        output_filename = "somef_output.json"
        cached_output_fpath = self.somef_output_path(url, commit_hash)

        if os.path.isfile(cached_output_fpath):
            with open(cached_output_fpath, encoding="utf-8") as f:
                report = json.load(f)

            self._cache[cache_key] = report
            return report

        with create_workspace(prefix="resqui-somef-") as workspace:
            container_workspace = workspace.container_path("/workspace")
            output_container_path = os.path.join(container_workspace, output_filename)
            output_fpath = os.path.join(workspace.local_path, output_filename)

            run_args = [
                "--rm",
                *workspace.docker_mount_args("/workspace"),
                "-e",
                f"SOMEF_REPO_URL={url}",
                "-e",
                f"SOMEF_OUTPUT_FILE={output_container_path}",
                "-e",
                f"SOMEF_COMMIT={commit_hash}",
                "-e",
                "SOMEF_DOWNLOAD_LIMIT_MB=1000",
            ]

            if self.context.github_token:
                run_args += ["-e", f"SOMEF_GITHUB_TOKEN={self.context.github_token}"]

            command = [
                "/bin/bash",
                "-lc",
                """
                set -e
                if [ -n "${SOMEF_GITHUB_TOKEN:-}" ]; then
                    somef describe \
                        -r "$SOMEF_REPO_URL" \
                        -o "$SOMEF_OUTPUT_FILE" \
                        -t 0.8 \
                        --commit "$SOMEF_COMMIT" \
                        --download-limit "$SOMEF_DOWNLOAD_LIMIT_MB" \
                        --github-token "$SOMEF_GITHUB_TOKEN"
                else
                    somef describe \
                        -r "$SOMEF_REPO_URL" \
                        -o "$SOMEF_OUTPUT_FILE" \
                        -t 0.8 \
                        --commit "$SOMEF_COMMIT" \
                        --download-limit "$SOMEF_DOWNLOAD_LIMIT_MB"
                fi
                """,
            ]
                
            result = self.executor.run(command, run_args=run_args)
            if not os.path.isfile(output_fpath):
                if result.returncode != 0:
                    raise ValueError(
                        "SoMEF Docker execution failed:\n"
                        f"stdout:\n{result.stdout}\n"
                        f"stderr:\n{result.stderr}"
                    )
                msg = (
                    "Error: SoMEF did not generate the expected output file "
                    f"named '{output_filename}'"
                )
                raise FileNotFoundError(msg)

            with open(output_fpath, encoding="utf-8") as f:
                report = json.load(f)

        os.makedirs(os.path.dirname(cached_output_fpath), exist_ok=True)
        with open(cached_output_fpath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self._cache[cache_key] = report

        return report

    def has_active_communication_channels(self, url, branch_hash_or_tag):
        
        communication_channel_fields = ("support_channels", "support", "contact")

        report = self.execute(url, branch_hash_or_tag)
        channels = []

        for field in communication_channel_fields:
            for item in report.get(field, []):
                result = item.get("result", {})
                values = [
                    result.get("value"),
                    result.get("name"),
                    result.get("email"),
                    result.get("url"),
                ]
                value = "; ".join(str(v).strip() for v in values if v)
                if value:
                    channels.append((field, value))

        success = bool(channels)
        output = "true" if success else "false"

        if success:
            evidence = "SoMEF found explicit communication channel metadata:\n"
            evidence += "\n".join(
                f"- {field}: {value}" for field, value in channels
            )
        else:
            evidence = (
                "No explicit SoMEF communication channel fields found. "
                "Checked fields: support_channels, support, contact."
            )

        return CheckResult(
            process=(
                "Checks whether SoMEF extracts explicit communication channel "
                "metadata from the repository using the support_channels, "
                "support, and contact fields."
            ),
            status_id="schema:CompletedActionStatus",
            output=output,
            evidence=evidence,
            success=success,
        )



    def software_id(self, url):
        return (
            url.removesuffix(".git")
            .replace("https://github.com/", "")
            .replace("http://github.com/", "")
            .rstrip("/")
            .replace("/", "_")
        )

    def ref_id(self, ref):
        return str(ref).replace("/", "_").replace(":", "_")

    def somef_output_path(self, url, commit_hash):
        return os.path.join(
            "tmp",
            "somef_outputs",
            self.software_id(url),
            self.ref_id(commit_hash),
            "somef_output.json",
        )

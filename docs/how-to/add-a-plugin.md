# Add an Indicator Plugin

This guide shows how to add a new quality indicator to resqui.

## 1. Create the plugin module

Add a new file under `src/resqui/plugins/`, for example `src/resqui/plugins/myplugin.py`.

## 2. Subclass `IndicatorPlugin`

```python
from resqui.plugins.base import IndicatorPlugin
from resqui.core import CheckResult


class MyPlugin(IndicatorPlugin):
    name = "MyPlugin"
    version = "1.0.0"
    id = "https://w3id.org/everse/software/MyPlugin"
    indicators = ["has_readme"]

    def __init__(self, context):
        # context.github_token and context.dashverse_token are available
        # Raise PluginInitError here if required credentials are missing
        pass

    def has_readme(self, url, branch_or_commit):
        # run your check here and return a CheckResult
        found = ...  # your check logic
        return CheckResult(
            process="Looks for a README file in the repository root.",
            status_id="schema:CompletedActionStatus" if found else "schema:FailedActionStatus",
            output="valid" if found else "missing",
            evidence="Found README." if found else "No README found.",
            success=found,
        )
```

### Using PythonExecutor

```python
from resqui.executors.python import PythonExecutor

class MyPlugin(IndicatorPlugin):
    def __init__(self, context):
        self.executor = PythonExecutor(packages=["some-package==1.2.3"])

    def my_indicator(self, url, branch_or_commit):
        result = self.executor.execute(f"""
import some_package
output = some_package.check("{url}")
print(output)
""")
        ...
```

### Using DockerExecutor

```python
from resqui.executors.docker import DockerExecutor

class MyPlugin(IndicatorPlugin):
    def __init__(self, context):
        self.executor = DockerExecutor("ghcr.io/org/image:latest")

    def my_indicator(self, url, branch_or_commit):
        result = self.executor.run(["check", url])
        ...
```

Both executors raise `ExecutorInitError` on startup failure (e.g. Docker not
available, pip install failed). resqui catches this and skips the plugin with a
warning rather than aborting the whole run.

## 3. Export from the plugins package

Add an import to `src/resqui/plugins/__init__.py`:

```python
from resqui.plugins.myplugin import MyPlugin
```

## 4. Reference it in a configuration file

```json
{
  "indicators": [
    {
      "name": "has_readme",
      "plugin": "MyPlugin",
      "@id": "missing"
    }
  ]
}
```

## 5. Verify

```bash
resqui indicators
```

Your plugin and its indicators should appear in the list.

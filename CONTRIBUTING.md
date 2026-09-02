# Contributing to resqui

Thanks for helping improve resqui.

## Scope of contributions

Contributions are most useful when they improve one of these areas:

- CLI behavior in src/resqui/cli.py and supporting core modules
- Indicator plugins in src/resqui/plugins/
- Executors in src/resqui/executors/
- Reference configurations in configurations/
- GitHub Action behavior in action.yml
- Tests in tests/
- User-facing docs in README.md

## Local setup

Use Python 3.9+.

```bash
python3 -m venv venv
source venv/bin/activate
make install-dev
```

## Make your change

1. Create a branch from main.
2. Keep changes focused and small.
3. If behavior changes, add or update tests in tests/.
4. If CLI options, action inputs, config format, or output semantics change, update README.md.

## Validate before opening a PR

Run:

```bash
make test
```

If your change affects runtime behavior, also run:

```bash
resqui -c configurations/basic.json -t <your_github_token>
```

If your change affects install or packaging, verify:

```bash
make install-dev
pip install .
```

If you changed formatting-sensitive files, you can run:

```bash
make black
```

## Plugin and indicator contributions

For new indicators or plugins:

- Add or update plugin code in src/resqui/plugins/
- Ensure indicator names map to plugin methods
- Return CheckResult values with clear evidence text
- Add or update matching entries in configurations/ when needed
- Add tests that cover success and failure paths

## Pull requests

Open a PR targeting main and complete the checklist in .github/PULL_REQUEST_TEMPLATE.md.

Include:

- A clear summary of what changed
- Validation commands you ran
- Any follow-up work that is out of scope for the PR

## Issues

Use the issue forms under .github/ISSUE_TEMPLATE/:

- Bug report
- Plugin or indicator request
- Usage question

These forms help maintainers reproduce problems and review changes quickly.

## Security and secrets

Do not commit tokens, credentials, or private data.

When sharing logs, remove sensitive values such as GitHub and DashVerse tokens.

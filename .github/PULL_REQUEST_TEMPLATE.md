## Summary

Describe the change in terms of `resqui`, the composite action in `action.yml`, a configuration under `configurations/`, or a plugin/executor under `src/resqui/`.

## Validation

- [ ] I ran `make test` locally, or I cannot run it and explained why.
- [ ] If I changed CLI behavior, configuration loading, or plugin results, I ran `resqui -c configurations/basic.json -t <token>` or explained why that was not possible.
- [ ] If I changed packaging or installation behavior, I verified `make install-dev` and `pip install .` still work.

## Review notes

- [ ] This PR targets `main`.
- [ ] I updated `README.md` if I changed CLI flags, action inputs, setup steps, output semantics, or the expected configuration format.
- [ ] I updated files under `configurations/` if the default or reference indicator sets changed.
- [ ] I added or updated tests in `tests/` when behavior changed.

## Related issue

Link the issue if there is one. If there is no issue, state the maintenance problem this PR resolves.

# Development workflow

1. Choose a stable issue ID from `PROJECT.md` or the imported GitHub issues.
2. Create a branch describing the change.
3. Implement the smallest coherent behavior and its focused checks.
4. Update the relevant reference, how-to, and changelog.
5. Run the tests, generated-role check, and strict documentation build.
6. Open a pull request with the concrete behavior change and validation.

CI runs the tests and Sphinx build. It saves the built documentation as an
Actions artifact. Public documentation hosting is an explicit later choice;
the initial documentation site is local.

## Validation commands

```bash
python -m unittest discover -s tests -v
```

```bash
python tools/render_roles.py --check
```

```bash
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

The repository includes fake-client tests for the model adapter. Account-level
API validation uses a synthetic example after local credentials are configured.

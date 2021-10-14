# Release checklist

## Patch release

- Check `pytest`

- Update release notes

## Minor release

## Major release

- Run `pre-commit autoupdate`

- Check README.md

- Check setup.py

    - Are classifiers up to date?
    - Is `python_requires` correct?
    - Python 3.6 is EOL on December 2021-12. Could drop support then.
    - Can we tighten any `install_requires` dependencies?

- Search for old version shims we can remove

    - "shim"
    - ` pikepdf.__version__`

- Search for deprecation: search all files for deprec*, etc.

- Check requirements in setup.cfg

- Delete `tests/cache`, do `pytest --runslow`, and update cache.

- Do `pytest --cov-report html`

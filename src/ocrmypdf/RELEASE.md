<!-- SPDX-FileCopyrightText: 2022 James R. Barlow -->
<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->

# Release checklist

## Patch release

- Check `pytest`

- Update release notes

## Minor release

## Major release

- Run `pre-commit autoupdate`

- Check README.md

- Check pyproject.toml

    - Are classifiers up to date?
    - Is `python_requires` correct?
    - Is it to drop support for older Pythons?
    - Can we tighten any `install_requires` dependencies?

- Search for old version shims we can remove

    - "shim"
    - ` pikepdf.__version__`

- Search for deprecation: search all files for deprec*, etc.

- Check requirements in setup.cfg

- Delete `tests/cache`, do `pytest --runslow`, and update cache.

- Do `pytest --cov-report html`

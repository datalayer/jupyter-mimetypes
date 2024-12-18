<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# Jupyter Representations

[![Github Actions Status](https://github.com/datalayer/jupyter-reprs/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-reprs/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-reprs)](https://pypi.org/project/jupyter-reprs)

TODO

To install the library, run the following command.

```bash
pip install jupyter_reprs
```

## Uninstall

To remove the library, run the following.

```bash
pip uninstall jupyter_reprs
```

## Contributing

### Development install

```bash
# Clone the repo to your local environment
# Change directory to the jupyter_nbmodel_client directory
# Install package in development mode - will automatically enable
# The server extension.
pip install -e ".[test,lint,typing]"
```

### Running Tests

Install dependencies:

```bash
pip install -e ".[test]"
```

To run the python tests, use:

```bash
pytest
```

### Development uninstall

```bash
pip uninstall jupyter_reprs
```

### Packaging the library

See [RELEASE](RELEASE.md)

<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# Jupyter MIME Types

[![Github Actions Status](https://github.com/datalayer/jupyter-mimetypes/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-mimetypes/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-mimetypes)](https://pypi.org/project/jupyter-mimetypes)
[![Python Version](https://img.shields.io/pypi/pyversions/jupyter-mimetypes)](https://pypi.org/project/jupyter-mimetypes)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)

A Python package that provides enhanced Jupyter representation capabilities through proxy objects, enabling efficient Apache Arrow-based serialization for pandas DataFrames/Series and pickle-based serialization for generic Python objects in Jupyter environments.

To install the library, run the following command.

```bash
pip install jupyter-mimetypes
```

## Features

- **Efficient Serialization**: Apache Arrow format for pandas DataFrames and Series
- **Universal Fallback**: Pickle-based serialization for any Python object
- **Jupyter Integration**: Seamless MIME bundle support for Jupyter display system
- **Type Safety**: Complete type annotations and mypy compatibility

## Quick Start

### Basic Object Serialization

```python
import pandas as pd
from jupyter_mimetypes import serialize_object, deserialize_object

# Create a pandas DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['New York', 'London', 'Tokyo']
})

# Serialize the DataFrame
data, metadata = serialize_object(df)
print(f"Serialized to {len(data)} MIME types: {list(data.keys())}")

# Deserialize back to original object
restored_df = deserialize_object(data, metadata)
print(f"Restored DataFrame shape: {restored_df.shape}")
```

### Working with Jupyter Kernels

Example using the [jupyter-kernel-client](https://github.com/datalayer/jupyter-kernel-client):

```python
import pandas as pd

from jupyter_kernel_client import KernelClient
from jupyter_mimetypes import get_variable, set_variable


# Connect to a Jupyter kernel
with KernelClient(server_url="http://localhost:8888", token=SERVER_TOKEN) as client:
    # Execute code in the kernel
    client.execute("""
    import pandas as pd
    import numpy as np

    # Create a large DataFrame with mixed types
    np.random.seed(42)
    df = pd.DataFrame({
        'values': np.random.randn(1000),
        'categories': np.random.choice(['A', 'B', 'C'], 1000),
        'integers': np.random.randint(1, 100, 1000)
    })
    """)

    # Retrieve the DataFrame from the kernel
    retrieved_df = client.get_variable("df")
    print(f"Retrieved DataFrame: {retrieved_df.shape}")

    np.random.seed(42)
    df2 = pd.DataFrame({
        'values': np.random.randn(1000),
        'categories': np.random.choice(['A', 'B', 'C'], 1000),
        'integers': np.random.randint(1, 100, 1000)
    })
    client.set_variable("df2", df2)
    client.execute("print(df2)")
```

## Uninstall

To remove the library, run the following.

```bash
pip uninstall jupyter-mimetypes
```

## Architecture

### Serialization Backends

- **Apache Arrow**: High-performance serialization for pandas DataFrames and Series
- **Pickle**: Universal Python object serialization as fallback

### Core Components

- **ProxyObject**: Wraps objects with custom `_repr_mimebundle_` methods
- **MIME Type Registry**: Maps object types to appropriate serialization functions
- **Base64 Encoding**: Ensures safe string transport of binary data
- **Type Detection**: Automatic selection of optimal serialization backend

## API Reference

### Core Functions

- `serialize_object(obj, mimetype=None)` - Serialize any Python object
- `deserialize_object(data, metadata)` - Deserialize from MIME bundle
- `get_variable(name, mimetype=None, globals_dict=None)` - Display variable with custom MIME types
- `set_variable(name, data, metadata, globals_dict)` - Set deserialized variable in namespace

### Supported MIME Types

- `application/vnd.apache.arrow.stream` - pandas DataFrames and Series
- `application/x-python-pickle` - Generic Python objects

## Contributing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/datalayer/jupyter-mimetypes.git
cd jupyter-mimetypes

# Install in development mode with all dependencies
pip install -e ".[test,lint,typing]"

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Code Quality

The project maintains high code quality standards:

- **Type Safety**: 100% mypy compliance with strict settings
- **Code Formatting**: Ruff for linting and formatting
- **Documentation**: NumPy-style docstrings with numpydoc validation
- **Testing**: Comprehensive test suite with 100+ tests

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jupyter_mimetypes

# Run specific test categories
pytest tests/test_api.py          # Core API tests
pytest tests/_io/                 # Serialization backend tests
pytest tests/test_integration.py  # Integration tests (requires Jupyter)
```

### Code Quality Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Individual checks
ruff check .                    # Linting
ruff format .                   # Formatting
mypy jupyter_mimetypes/         # Type checking
```

### Development Guidelines

- All new features must include comprehensive tests
- Documentation must follow NumPy docstring standards
- Type annotations are required for all public APIs
- Integration tests should cover real-world usage scenarios

## Release Process

See [RELEASE.md](RELEASE.md) for detailed release instructions.

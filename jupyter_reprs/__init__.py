# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Dynamically inject new Jupyter representation to
some objects."""

__version__ = "0.0.1"

from .common import DEFAULT_DATA_MIMETYPE, mimebundle_to_object

# Import to load monkey patches
from .pandas import *  # noqa F403

__all__ = ["DEFAULT_DATA_MIMETYPE", "mimebundle_to_object"]

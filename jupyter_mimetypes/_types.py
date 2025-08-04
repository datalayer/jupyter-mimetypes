# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Type definitions for Jupyter MIME types and serialization."""

from typing import Any, Callable, Union

from typing_extensions import TypeAlias

ModuleTypeTuple: TypeAlias = tuple[str, str]
SerializeFunc: TypeAlias = Callable[..., Union[str, bytes]]
DeserializeFunc: TypeAlias = Callable[..., Any]
MIMETypeFuncs: TypeAlias = tuple[str, SerializeFunc, DeserializeFunc]
MIMETypeMapping: TypeAlias = dict[ModuleTypeTuple, MIMETypeFuncs]

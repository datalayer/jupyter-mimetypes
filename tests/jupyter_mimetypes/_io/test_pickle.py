# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Tests for pickle serialization functions."""

import pickle

import numpy as np
import pytest
import torch

from jupyter_mimetypes._io._pickle import _deserialize_pickle as deserialize_pickle
from jupyter_mimetypes._io._pickle import _serialize_pickle as serialize_pickle


class TestPickleSerialization:
    """Test suite for pickle serialization functions."""

    def test_pickle_comprehensive_data_types(self):
        """Test pickle serialization/deserialization with comprehensive data types."""
        # Comprehensive test cases covering all data types
        test_cases = [
            # Basic types
            "hello world",
            42,
            3.14159,
            True,
            False,
            None,
            # Collections
            [1, 2, 3, "hello"],
            {"key": "value", "number": 42},
            (1, 2, "three"),
            {1, 2, 3, "unique"},
            # Empty objects
            "",
            [],
            {},
            (),
            set(),
            # Nested structures
            {
                "list": [1, 2, {"nested": "dict"}],
                "dict": {"inner": [1, 2, 3]},
                "tuple": (1, [2, 3], {"key": "value"}),
            },
            # Add numpy arrays if available
            np.array([1, 2, 3, 4, 5]),  # 1D array
            np.array([[1, 2], [3, 4]]),  # 2D array
            np.array([1.1, 2.2, 3.3], dtype=np.float32),  # Float array
            np.array([True, False, True]),  # Boolean array
            np.array([]),  # Empty array
            np.random.randn(10, 5),  # Random array
            # Add PyTorch tensors if available
            torch.tensor([1, 2, 3, 4, 5]),  # 1D tensor
            torch.tensor([[1.0, 2.0], [3.0, 4.0]]),  # 2D tensor
            torch.randn(5, 3),  # Random tensor
            torch.zeros(3, 3),  # Zero tensor
            torch.ones(2, 4),  # Ones tensor
            torch.tensor([]),  # Empty tensor
        ]

        for obj in test_cases:
            # Test serialize_pickle
            serialized = serialize_pickle(obj)
            assert isinstance(serialized, bytes)
            assert len(serialized) > 0

            # Test deserialize_pickle
            restored_with_function = deserialize_pickle(serialized)
            if isinstance(obj, (np.ndarray, torch.Tensor)):
                assert (restored_with_function == obj).all()
            else:
                assert restored_with_function == obj

    def test_deserialize_pickle_with_metadata(self):
        """Test deserialize_pickle with metadata parameter."""
        test_obj = {"key": "value"}
        pickled_data = pickle.dumps(test_obj)

        # Metadata should be ignored for pickle deserialization
        metadata = {"type": ("dict", "dict"), "extra": "ignored"}
        restored = deserialize_pickle(pickled_data, metadata)

        assert restored == test_obj

    def test_deserialize_pickle_none_metadata(self):
        """Test deserialize_pickle with None metadata."""
        test_obj = {"key": "value"}
        pickled_data = pickle.dumps(test_obj)

        # Should work with None metadata
        restored = deserialize_pickle(pickled_data, None)
        assert restored == test_obj

    def test_roundtrip_pickle_serialization(self):
        """Test complete roundtrip pickle serialization."""
        test_cases = [
            "simple string",
            [1, 2, 3, "mixed", {"nested": "dict"}],
            {"complex": {"nested": {"structure": [1, 2, 3]}}},
            (1, 2, 3, [4, 5, 6]),
            {1, 2, 3, "set_element"},
        ]

        for original_obj in test_cases:
            # Serialize
            serialized = serialize_pickle(original_obj)

            # Deserialize
            restored = deserialize_pickle(serialized)

            # Verify
            assert restored == original_obj
            assert type(restored) is type(original_obj)

    def test_pickle_error_handling(self):
        """Test pickle error handling with invalid data."""
        # Test with invalid pickle data
        invalid_data = b"this_is_not_valid_pickle_data"

        with pytest.raises(
            (Exception, pickle.UnpicklingError)
        ):  # pickle.loads will raise various exceptions
            deserialize_pickle(invalid_data)

    def test_pickle_function_consistency(self):
        """Test that our pickle functions are consistent with standard pickle."""
        test_obj = {"consistency": "test", "numbers": [1, 2, 3]}

        # Serialize with our function
        our_serialized = serialize_pickle(test_obj)

        # Serialize with standard pickle
        std_serialized = pickle.dumps(test_obj)

        # Both should deserialize to the same object
        our_restored = deserialize_pickle(our_serialized)
        std_restored = pickle.loads(std_serialized)  # noqa: S301
        cross_restored1 = deserialize_pickle(std_serialized)
        cross_restored2 = pickle.loads(our_serialized)  # noqa: S301

        assert our_restored == test_obj
        assert std_restored == test_obj
        assert cross_restored1 == test_obj
        assert cross_restored2 == test_obj

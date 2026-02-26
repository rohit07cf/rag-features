"""Batch processing utilities."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def batch_items(items: list[T], batch_size: int) -> list[list[T]]:
    """Split a list into batches of given size."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

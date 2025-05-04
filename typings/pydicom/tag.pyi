from __future__ import annotations

from typing import Any

class BaseTag(int):
    """Represents a DICOM element (group, element) tag.

    Tags are represented as an :class:`int`.
    """
    # Override comparisons so can convert "other" to Tag as necessary
    #   See Ordering Comparisons at:
    #   http://docs.python.org/dev/3.0/whatsnew/3.0.html
    def __le__(self, other: Any) -> Any:
        """Return ``True`` if `self`  is less than or equal to `other`."""

    def __lt__(self, other: Any) -> Any:
        """Return ``True`` if `self` is less than `other`."""

    def __ge__(self, other: Any) -> Any:
        """Return ``True`` if `self` is greater than or equal to `other`."""

    def __gt__(self, other: Any) -> Any:
        """Return ``True`` if `self` is greater than `other`."""

    def __eq__(self, other: Any) -> Any:
        """Return ``True`` if `self` equals `other`."""
        # Check if comparing with another Tag object; if not, create a temp one
    def __ne__(self, other: Any) -> Any:
        """Return ``True`` if `self` does not equal `other`."""

    __hash__ = int.__hash__

    def __str__(self) -> str:
        """Return the tag value as a hex string '(gggg, eeee)'."""

    __repr__ = __str__

    @property
    def json_key(self) -> str:
        """Return the tag value as a JSON key string 'GGGGEEEE'."""

    @property
    def group(self) -> int:
        """Return the tag's group number as :class:`int`."""

    @property
    def element(self) -> int:
        """Return the tag's element number as :class:`int`."""

    elem = element  # alternate syntax

    @property
    def is_private(self) -> bool:
        """Return ``True`` if the tag is private (has an odd group number)."""

    @property
    def is_private_creator(self) -> bool:
        """Return ``True`` if the tag is a private creator.

        .. versionadded:: 1.1
        """

    @property
    def private_creator(self) -> BaseTag:
        """Return the private creator tag for the given tag.
        The result is meaningless if this is not a private tag.

        .. versionadded:: 2.4
        """

TagListType = list[int] | list[str] | list[tuple[int, int]] | list[BaseTag]

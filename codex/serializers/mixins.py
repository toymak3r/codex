"""Serializer mixins."""
from datetime import datetime

from rest_framework.serializers import (
    BooleanField,
    DecimalField,
    Field,
    IntegerField,
    Serializer,
)


UNIONFIX_PREFIX = "unionfix_"


class TimestampField(Field):
    """Datetime Field represented as an integer."""

    def to_representation(self, value: datetime):
        """Return integer timestamp from datetime."""
        return value.timestamp()


class BrowserAggregateSerializerMixin(Serializer):
    """Mixin for browser & metadata serializers."""

    # Aggregate Annotations
    child_count = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "child_count")
    cover_pk = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "cover_pk")
    cover_updated_at = TimestampField(
        read_only=True, source=UNIONFIX_PREFIX + "cover_updated_at"
    )

    # UserBookmark annotations
    bookmark = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "bookmark")
    finished = BooleanField(read_only=True, source=UNIONFIX_PREFIX + "finished")
    progress = DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        coerce_to_string=False,
        source=UNIONFIX_PREFIX + "progress",
    )


BROWSER_AGGREGATE_ORDERED_UNIONFIX_VALUES_MAP = dict(
    # A map for ordering the metadata values() properly with the UNIONFIX_PREFIX
    # Fixes Django's requirement that unions have the same field order, but Django
    # provides no mechanism to actually order fields.
    # used in views/metadata
    (
        (UNIONFIX_PREFIX + field, field)
        for field in sorted(BrowserAggregateSerializerMixin().get_fields())
    )
)

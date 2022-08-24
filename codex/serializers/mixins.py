"""Serializer mixins."""
from datetime import datetime

from django.db.models import F
from rest_framework.serializers import (
    BooleanField,
    CharField,
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


class BrowserAggregateBaseSerializerMixin(Serializer):
    """Mixin for browser, opds & metadata serializers."""

    group = CharField(read_only=True, max_length=1, source=UNIONFIX_PREFIX + "group")

    # Aggregate Annotations
    child_count = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "child_count")
    cover_pk = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "cover_pk")

    # Bookmark annotations
    page = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "page")


class BrowserAggregateSerializerMixin(BrowserAggregateBaseSerializerMixin):
    """Mixin for browser & metadata serializers."""

    finished = BooleanField(read_only=True, source=UNIONFIX_PREFIX + "finished")
    progress = DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        coerce_to_string=False,
        source=UNIONFIX_PREFIX + "progress",
    )


class BrowserCardOPDSBaseSerializer(BrowserAggregateSerializerMixin):
    """Common base for Browser Card and OPDS serializer."""

    pk = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "pk")
    publisher_name = CharField(
        read_only=True, source=UNIONFIX_PREFIX + "publisher_name"
    )
    series_name = CharField(read_only=True, source=UNIONFIX_PREFIX + "series_name")
    volume_name = CharField(read_only=True, source=UNIONFIX_PREFIX + "volume_name")
    name = CharField(read_only=True, source=UNIONFIX_PREFIX + "name")
    issue = DecimalField(
        max_digits=16,
        decimal_places=3,
        read_only=True,
        coerce_to_string=False,
        source=UNIONFIX_PREFIX + "issue",
    )
    issue_suffix = CharField(read_only=True, source=UNIONFIX_PREFIX + "issue_suffix")
    order_value = CharField(read_only=True, source=UNIONFIX_PREFIX + "order_value")
    page_count = IntegerField(read_only=True, source=UNIONFIX_PREFIX + "page_count")


def get_serializer_values_map(serializers, copy_only=False):
    """Create map for ordering values() properly with the UNIONFIX_PREFIX."""
    # Fixes Django's requirement that unions have the same field order, but Django
    # provides no mechanism to actually order fields.
    fields = {}
    for serializer in serializers:
        fields.update(serializer().get_fields())
    fields = sorted(fields)
    result = {}
    for field in fields:
        if copy_only:
            val = field
        else:
            val = F(field)
        result[UNIONFIX_PREFIX + field] = val
    return result

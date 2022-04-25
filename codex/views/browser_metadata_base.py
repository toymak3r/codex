"""Base view for metadata annotations."""
from os import sep

from django.db.models import (
    Avg,
    BooleanField,
    CharField,
    Count,
    DecimalField,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Cast, Coalesce, NullIf, Reverse, Right, StrIndex

from codex.models import Comic, Folder, Imprint, Publisher, Series, Volume
from codex.serializers.mixins import UNIONFIX_PREFIX
from codex.views.browser_base import BrowserBaseView


class BrowserMetadataBaseView(BrowserBaseView):
    """Base class for views that need special metadata annotations."""

    _ORDER_BY_FIELD_ALIASES = {"search_score": "searchresult__score"}
    _ORDER_AGGREGATE_FUNCS = {
        "age_rating": Avg,
        "community_rating": Avg,
        "created_at": Min,
        "critical_rating": Avg,
        "date": Min,
        "page_count": Sum,
        "path": Min,
        "size": Sum,
        "updated_at": Min,
        "searchresult__score": Min,
    }
    _NO_SEARCH_SCORE = Value(None, IntegerField())
    _UNIONFIX_DEFAULT_ORDERING = tuple(
        UNIONFIX_PREFIX + field.replace("__", "_") for field in Comic.ORDERING
    )
    _ORDER_VALUE_ORDERING = (UNIONFIX_PREFIX + "order_value", UNIONFIX_PREFIX + "pk")
    GROUP_MODEL_MAP = {
        "r": None,
        "p": Publisher,
        "i": Imprint,
        "s": Series,
        "v": Volume,
        BrowserBaseView.COMIC_GROUP: Comic,
        BrowserBaseView.FOLDER_GROUP: Folder,
    }
    DEFAULT_ORDER_KEY = "sort_name"

    @staticmethod
    def _cover_subquery(cover_comics, field):
        """Create cover subquery for each field."""
        return Subquery(cover_comics.values(f"comic__{field}")[:1])

    def _annotate_cover_path(self, queryset, model):
        """Annotate the query set for the coverpath for the sort."""
        # Select comics for the children by an outer ref for annotation
        # Order the descendant comics by the sort argumentst
        if model == Comic:
            cover_updated_at = F("updated_at")
        else:
            # This creates two subqueries. It would be better condensed into one.
            # but there's no way to annotate an object or multiple values.
            order_by = self.get_order_by(Comic, for_cover_path=True)
            cover_comics = queryset.filter(pk=OuterRef("pk")).order_by(*order_by)
            cover_path = self._cover_subquery(cover_comics, "cover_path")
            queryset = queryset.annotate(cover_path=cover_path)
            cover_updated_at = self._cover_subquery(cover_comics, "updated_at")
        queryset = queryset.annotate(cover_updated_at=cover_updated_at)
        return queryset

    def _annotate_page_count(self, obj_list):
        """Hoist up total page_count of children."""
        # Used for sorting and progress
        page_count_sum = Sum("comic__page_count")
        obj_list = obj_list.annotate(page_count=page_count_sum)
        return obj_list

    def _get_userbookmark_filter(self, is_model_comic):
        """Get a filter for my session or user defined bookmarks."""
        ubm_rel = self.get_ubm_rel(is_model_comic)

        if self.request.user.is_authenticated:
            my_bookmarks_kwargs = {f"{ubm_rel}__user": self.request.user}
        else:
            my_bookmarks_kwargs = {
                f"{ubm_rel}__session__session_key": self.request.session.session_key
            }
        return Q(**my_bookmarks_kwargs)

    def _annotate_bookmarks(self, obj_list, is_model_comic):
        """Hoist up bookmark annoations."""
        ub_filter = self._get_userbookmark_filter(is_model_comic)

        ubm_rel = self.get_ubm_rel(is_model_comic)

        # Hoist up: are the children finished or unfinished?
        finished_aggregate = Cast(
            NullIf(
                Coalesce(
                    Avg(  # distinct average of user's finished values
                        f"{ubm_rel}__finished",
                        filter=ub_filter,
                        distinct=True,
                        output_field=DecimalField(max_digits=2, decimal_places=2),
                    ),
                    False,  # Null db values counted as False
                ),
                Value(0.5),  # Null result if mixed true & false
            ),
            BooleanField(),  # Finally ends up as a ternary boolean
        )

        # Hoist up the bookmark
        bookmark_sum = Sum(f"{ubm_rel}__bookmark", filter=ub_filter)

        obj_list = obj_list.annotate(finished=finished_aggregate, bookmark=bookmark_sum)

        return obj_list

    @staticmethod
    def _annotate_progress(queryset):
        """Compute progress for each member of a queryset."""
        # Requires bookmark and annotation hoisted from userbookmarks.
        # Requires page_count native to comic or aggregated
        queryset = queryset.annotate(
            progress=Coalesce(F("bookmark") * 100.0 / F("page_count"), 0.0)
        )
        return queryset

    @staticmethod
    def _get_path_query_func(field):
        """Use the db to get only the filename."""
        return Right(field, StrIndex(Reverse(field), Value(sep)) - 1)  # type: ignore

    def get_aggregate_func(self, order_key, model, autoquery_pk=None):
        """Get a complete function for aggregating an attribute."""
        # Get field from order_key
        if order_key == "search_score":
            if not autoquery_pk:
                return self._NO_SEARCH_SCORE
            field = "searchresult__score"
        elif order_key == "sort_name" or not order_key:
            field = None
        else:
            field = order_key

        # Determine order func
        if not field:
            # use default sorting.
            func = Value(None, output_field=CharField())
        elif field == "path" and model in (Comic, Folder):
            # special path sorting.
            func = self._get_path_query_func(field)
        elif model == Comic:
            # agg_none uses group fields not comic fields.
            func = F(field)
        else:
            # order by aggregate.

            # get agg_func
            agg_func = self._ORDER_AGGREGATE_FUNCS[field]
            if agg_func == Min and self.params.get("order_reverse"):
                agg_func = Max

            # get full_field
            full_field = "comic__" + field
            if field == "path":
                full_field = self._get_path_query_func(full_field)

            filters = Q(comic__searchresult__query=autoquery_pk)
            func = agg_func(full_field, filters=filters)
        return func

    def annotate_common_aggregates(self, qs, model):
        """Annotate common aggregates between browser and metadata."""
        is_model_comic = model == Comic
        qs = self._annotate_cover_path(qs, model)
        if is_model_comic:
            child_count_sum = Value(1, IntegerField())
        else:
            qs = self._annotate_page_count(qs)
            child_count_sum = Count("comic__pk", distinct=True)
        qs = qs.annotate(child_count=child_count_sum)
        qs = self._annotate_bookmarks(qs, is_model_comic)
        qs = self._annotate_progress(qs)
        return qs

    def get_order_by(self, model, for_cover_path=False):
        """
        Create the order_by list.

        Order on pk to give duplicates a consistent position.
        """
        # order_prefix
        reverse = self.params.get("order_reverse")
        prefix = "-" if reverse else ""

        # order_fields
        order_key = self.params.get("order_by", self.DEFAULT_ORDER_KEY)
        if for_cover_path:
            prefix += "comic__"
            field = self._ORDER_BY_FIELD_ALIASES.get(order_key, order_key)
            if field == "sort_name" or not field:
                ordering = Comic.ORDERING
            else:
                ordering = (field, "pk")
        elif order_key == "sort_name" or not order_key:
            # Use default sort
            if model in (Comic, Folder):
                ordering = self._UNIONFIX_DEFAULT_ORDERING
            else:
                ordering = model.ORDERING
        else:
            # Use annotated order_value
            ordering = self._ORDER_VALUE_ORDERING

        # order_by
        # add prefixes to all order_by fields
        ordering = (prefix + field for field in ordering)
        return ordering

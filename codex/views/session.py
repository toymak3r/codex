"""Manage user sessions with appropriate defaults."""
from abc import ABC
from copy import deepcopy

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from codex.serializers.choices import DEFAULTS
from codex.settings.logging import get_logger
from codex.views.auth import IsAuthenticatedOrEnabledNonUsers


LOG = get_logger(__name__)


class SessionViewBaseBase(GenericAPIView, ABC):
    """Generic Session View."""

    # Must override both of these
    SESSION_KEY = "UNDEFINED"
    SESSION_DEFAULTS = {}

    @classmethod
    def _get_source_values_or_set_defaults(cls, defaults_dict, source_dict, data):
        """Recursively copy source_dict values into data or use defaults."""
        result = deepcopy(data)
        for key, default_value in defaults_dict.items():
            result[key] = source_dict.get(key, default_value)
            if result[key] is None:
                # extra check for migrated or corrupt data
                result[key] = default_value
            if isinstance(default_value, dict):
                result[key] = cls._get_source_values_or_set_defaults(
                    default_value, source_dict.get(key, {}), result[key]
                )
        return result

    def get_from_session(self, key):  # only used by frontend
        """Get one key from the session or its default."""
        session = self.request.session.get(self.SESSION_KEY, self.SESSION_DEFAULTS)
        value = session.get(key, self.SESSION_DEFAULTS[key])
        return value

    def save_params_to_session(self, params):  # reader session & browser final
        """Save the session from params with defaults for missing values."""
        try:
            data = self._get_source_values_or_set_defaults(
                self.SESSION_DEFAULTS, params, {}
            )
            self.request.session[self.SESSION_KEY] = data
            self.request.session.save()
        except Exception as exc:
            LOG.warning(f"Saving params to session: {exc}")


class BrowserSessionViewBase(SessionViewBaseBase, ABC):
    """Browser session base."""

    CREDIT_PERSON_UI_FIELD = "creators"
    _DYNAMIC_FILTER_DEFAULTS = {
        "age_rating": [],
        "autoquery": "",
        "characters": [],
        "country": [],
        CREDIT_PERSON_UI_FIELD: [],
        "community_rating": [],
        "critical_rating": [],
        "decade": [],
        "format": [],
        "genres": [],
        "language": [],
        "locations": [],
        "read_ltr": [],
        "series_groups": [],
        "story_arcs": [],
        "tags": [],
        "teams": [],
        "year": [],
    }
    FILTER_ATTRIBUTES = frozenset(_DYNAMIC_FILTER_DEFAULTS.keys())
    SESSION_DEFAULTS = {
        "filters": {
            "bookmark": DEFAULTS["bookmarkFilter"],
            **_DYNAMIC_FILTER_DEFAULTS,
        },
        "autoquery": DEFAULTS["autoquery"],
        "top_group": DEFAULTS["topGroup"],
        "order_by": DEFAULTS["orderBy"],
        "order_reverse": False,
        "show": DEFAULTS["show"],
        "route": DEFAULTS["route"],
    }
    SESSION_KEY = "browser"


class ReaderSessionViewBase(SessionViewBaseBase, ABC):
    """Reader session base."""

    SESSION_KEY = "reader"
    SESSION_DEFAULTS = {"fit_to": DEFAULTS["fitTo"], "two_pages": False}


class SessionViewBase(SessionViewBaseBase, ABC):
    """Session view for retrieving stored settings."""

    permission_classes = [IsAuthenticatedOrEnabledNonUsers]

    serializer_class = Serializer  # must override

    def load_params_from_session(self):
        """Set the params from view session, creating missing values from defaults."""
        session = self.request.session.get(self.SESSION_KEY, self.SESSION_DEFAULTS)
        return self._get_source_values_or_set_defaults(
            self.SESSION_DEFAULTS, session, {}
        )

    def get(self, request, *args, **kwargs):
        """Get session settings."""
        params = self.load_params_from_session()
        serializer = self.get_serializer(params)
        return Response(serializer.data)

    @extend_schema(responses=None)
    def put(self, request, *args, **kwargs):
        """Update session settings."""
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        self.save_params_to_session(serializer.validated_data)
        return Response()

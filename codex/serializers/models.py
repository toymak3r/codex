"""Serializers for codex models."""
import pycountry

from rest_framework.serializers import (
    CharField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from codex.models import (
    Bookmark,
    Character,
    Comic,
    Credit,
    CreditPerson,
    CreditRole,
    Genre,
    Imprint,
    LibrarianStatus,
    Location,
    NamedModel,
    Publisher,
    Series,
    SeriesGroup,
    StoryArc,
    Tag,
    Team,
    Volume,
)


class PyCountrySerializer(Serializer):
    """
    PyCountry tag serializer to include long names.

    Takes a single string value and serializes the value to
    a pk attribute and a pycountry long name lookup of that value to
    the name.
    """

    LOOKUP_MODULE = pycountry.countries

    pk = SerializerMethodField()
    name = SerializerMethodField()

    class Meta:
        """Abstract class."""

        abstract = True

    def get_pk(self, obj):
        """Return submitted value as the key."""
        return obj

    @staticmethod
    def lookup_name(lookup_module, name):
        """Lookup the name with pycountry, just copy the key on fail."""
        if name is None:
            # This never seems to get called so I do it on the front end.
            return "None"
        if len(name) == 2:
            # fix for https://github.com/flyingcircusio/pycountry/issues/41
            lookup_obj = lookup_module.get(alpha_2=name)
        else:
            lookup_obj = lookup_module.lookup(name)
        if lookup_obj:
            value = lookup_obj.name
        else:
            # If lookup fails, return the key as the name
            value = name
        return value

    def get_name(self, obj):
        """Lookup the name with pycountry, just copy the key on fail."""
        return self.lookup_name(self.LOOKUP_MODULE, obj)


class LanguageSerializer(PyCountrySerializer):
    """Pycountry serializer for language field."""

    LOOKUP_MODULE = pycountry.languages


class CountrySerializer(PyCountrySerializer):
    """Pycountry serializer for country field."""

    pass


class NamedModelMeta:
    """Meta class for named models."""

    fields = ("pk", "name")


##########
# Groups #
##########


class GroupModelMeta:
    """Meta class for group models."""

    fields = NamedModelMeta.fields


class NamedModelSerializer(ModelSerializer):
    """A common class for NamedModels."""

    class Meta(NamedModelMeta):
        """Not Abstract."""

        model = Character  # XXX GENERIC SPECIFIC


class GroupModelSerializer(NamedModelSerializer):
    """A common class for BrowserGroupModels."""

    class Meta:
        """Abstract class."""

        abstract = True


class PublisherSerializer(GroupModelSerializer):
    """Publisher Model."""

    class Meta(GroupModelMeta):
        """Configure model."""

        model = Publisher


class ImprintSerializer(GroupModelSerializer):
    """Imprint Model."""

    class Meta(GroupModelMeta):
        """Configure model."""

        model = Imprint


class SeriesSerializer(GroupModelSerializer):
    """Series Model."""

    class Meta(GroupModelMeta):
        """Configure model."""

        model = Series


class VolumeSerializer(GroupModelSerializer):
    """Volume Model."""

    class Meta(GroupModelMeta):
        """Configure model."""

        model = Volume


##############
# ManyToMany #
##############


class CreditPersonSerializer(NamedModelSerializer):
    """CreditPerson model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = CreditPerson


class CreditRoleSerializer(NamedModelSerializer):
    """CreditRole model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = CreditRole


class CreditSerializer(ModelSerializer):
    """Credit model serializer."""

    role = CreditRoleSerializer()
    person = CreditPersonSerializer()

    class Meta:
        """Model spec."""

        model = Credit
        fields = ("pk", "person", "role")
        depth = 1


class CharacterSerializer(NamedModelSerializer):
    """Character model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = Character


class GenreSerializer(NamedModelSerializer):
    """Genre model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = Genre


class LocationSerializer(NamedModelSerializer):
    """Location model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = Location


class SeriesGroupSerializer(NamedModelSerializer):
    """SeriesGroup model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = SeriesGroup


class StoryArcSerializer(NamedModelSerializer):
    """StoryArc model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = StoryArc


class TagSerializer(NamedModelSerializer):
    """Tag model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = Tag


class TeamSerializer(NamedModelSerializer):
    """Team model."""

    class Meta(NamedModelMeta):
        """Configure model."""

        model = Team


class ComicSerializer(ModelSerializer):
    """Serialize a comic object for the metadata dialog."""

    # Annotations
    issue_count = IntegerField(allow_null=True)
    volume_count = IntegerField(allow_null=True)

    # Special Serialization with pycountry
    country = CountrySerializer(allow_null=True)
    language = LanguageSerializer(allow_null=True)

    # FKs
    publisher = PublisherSerializer(allow_null=True)
    imprint = ImprintSerializer(allow_null=True)
    series = SeriesSerializer(allow_null=True)
    volume = VolumeSerializer(allow_null=True)

    # ManyToMany
    characters = CharacterSerializer(many=True, allow_null=True)
    genres = GenreSerializer(many=True, allow_null=True)
    locations = LocationSerializer(many=True, allow_null=True)
    series_groups = SeriesGroupSerializer(many=True, allow_null=True)
    story_arcs = StoryArcSerializer(
        many=True,
        allow_null=True,
    )
    tags = TagSerializer(many=True, allow_null=True)
    teams = TeamSerializer(many=True, allow_null=True)
    credits = CreditSerializer(many=True, allow_null=True)

    class Meta:
        """Configure the model."""

        model = Comic
        exclude = ("folders", "parent_folder", "stat")
        depth = 1


class LibrarianStatusSerializer(ModelSerializer):
    """Serializer Librarian task statuses."""

    class Meta:
        """Configure the model."""

        model = LibrarianStatus
        exclude = ("active", "created_at", "updated_at")


class BookmarkSerializer(ModelSerializer):
    """Serializer Bookmark."""

    class Meta:
        """Configure the model."""

        model = Bookmark
        exclude = ("id", "user", "session", "comic", "created_at", "updated_at")


class BookmarkFinishedSerializer(ModelSerializer):
    """The finished field of the Bookmark."""

    class Meta:
        """Model spec."""

        model = Bookmark
        fields = ("finished",)

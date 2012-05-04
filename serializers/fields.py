from django.utils.encoding import is_protected_type, smart_unicode
from django.db.models.related import RelatedObject


class Field(object):
    creation_counter = 0

    def __init__(self, source=None, label=None, serialize=None):
        self.source = source
        self.label = label
        if serialize:
            self.serialize = serialize
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def _serialize_field(self, obj, field_name, parent):
        """
        The entry point into a field, as called by it's parent serializer.
        """
        if self.source == '*':
            return self.serialize(obj)

        field_name = self.source or field_name
        return self.serialize_field(obj, field_name)

    def serialize_field(self, obj, field_name):
        """
        Given the parent object and the field name, returns the field value
        that should be serialized.
        """
        return self.serialize(getattr(obj, field_name))

    def serialize(self, obj):
        """
        Serializes the field's value into it's simple representation.
        """
        if is_protected_type(obj):
            return obj
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return smart_unicode(obj)


class RelatedField(Field):
    """
    A base class for model related fields or related managers.
    Subclass this and override `serialize` to define custom behaviour when
    serializing related objects.
    """

    def serialize_field(self, obj, field_name):
        obj = getattr(obj, field_name)
        if obj.__class__.__name__ in ('RelatedManager', 'ManyRelatedManager'):
            return [self.serialize(item) for item in obj.all()]
        return self.serialize(obj)


class PrimaryKeyRelatedField(Field):
    """
    Serializes a model related field or related manager to a pk value.
    """

    # Note the we don't inherit from ModelRelatedField's implementation,
    # as we want to get the raw database value directly.
    #
    # An alternative implementation would simply be this...
    #
    # class PrimaryKeyRelatedField(RelatedField):
    #     def serialize(self, obj):
    #         return obj.pk

    def serialize_field(self, obj, field_name):
        try:
            obj = obj.serializable_value(field_name)
        except AttributeError:
            field = obj._meta.get_field_by_name(field_name)[0]
            obj = getattr(obj, field_name)
            if obj.__class__.__name__ == 'RelatedManager':
                return [item.pk for item in obj.all()]
            elif isinstance(field, RelatedObject):
                return obj.pk
            raise
        if obj.__class__.__name__ == 'ManyRelatedManager':
            return [item.pk for item in obj.all()]
        return obj


class NaturalKeyRelatedField(RelatedField):
    def serialize(self, obj):
        return obj.natural_key()


class ModelNameField(Field):
    """
    Serializes the model instance's model name.  Eg. 'auth.User'.
    """
    def serialize_field(self, obj, field_name):
        return smart_unicode(obj._meta)

from django.utils.encoding import is_protected_type, smart_unicode
from django.db.models.related import RelatedObject


class Field(object):
    creation_counter = 0

    def __init__(self, source=None, label=None):
        self.source = source
        self.label = label
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def initialize(self, parent):
        self.parent = parent
        # self.stack = parent.stack[:]

    def serialize(self, obj):
        raise NotImplementedError

    def get_field_value(self, obj, field_name):
        return getattr(obj, field_name)

    def serialize_field(self, obj, field_name):
        if self.source == '*':
            return self.serialize(obj)

        field_name = self.source or field_name
        obj = self.get_field_value(obj, field_name)
        return self.serialize(obj)


class ValueField(Field):
    """
    Basic serialization into primative types.
    """
    def serialize(self, obj):
        if is_protected_type(obj):
            return obj
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return smart_unicode(obj)


class ModelField(Field):
    """
    Serializes the model instance field to a flat value.
    """
    def serialize(self, obj):
        return obj

    def get_field_value(self, obj, field_name):
        try:
            return obj.serializable_value(field_name)
        except AttributeError:
            field = obj._meta.get_field_by_name(field_name)[0]
            if isinstance(field, RelatedObject):
                return getattr(obj, field_name).pk
            raise


class ModelNameField(Field):
    """
    Serializes the model instance's model name.  Eg. 'auth.User'.
    """
    def serialize(self, obj):
        return smart_unicode(obj._meta)

    def get_field_value(self, obj, field_name):
        return obj

from django.utils.encoding import is_protected_type, smart_unicode


class Field(object):
    creation_counter = 0

    def __init__(self, source=None, label=None):
        self.source = source
        self.label = label
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def initialize(self, parent):
        self.parent = parent

    def serialize(self, obj):
        raise NotImplementedError

    def serialize_field(self, obj, field_name):
        return self.serialize(getattr(obj, field_name))

    def _serialize_field(self, obj, field_name):
        if self.source == '*':
            return self.serialize(obj)
        field_name = self.source or field_name
        return self.serialize_field(obj, field_name)


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


class FlatModelField(Field):
    """
    Serializes the model instance field to a flat value.
    """
    def serialize_field(self, obj, field_name):
        return obj.serializable_value(field_name)


class ModelNameField(Field):
    """
    Serializes the model instance's model name.  Eg. 'auth.User'.
    """
    def serialize_field(self, obj, field_name):
        return smart_unicode(obj._meta)

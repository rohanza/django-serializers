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

    def serialize(self, obj):
        """
        Serializes the field's value into it's simple representation.
        """
        if is_protected_type(obj):
            return obj
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return smart_unicode(obj)

    def get_field_value(self, obj, field_name):
        """
        Given the parent object and the field name, returns the field value
        that should be serialized.
        """
        return getattr(obj, field_name)

    def serialize_field(self, obj, field_name, parent):
        """
        The entry point into a field, as called by it's parent serializer.
        """
        if self.source == '*':
            return self.serialize(obj)

        field_name = self.source or field_name
        obj = self.get_field_value(obj, field_name)
        return self.serialize(obj)


class ModelField(Field):
    """
    Serializes the model instance field to a flat value.
    """
    def serialize(self, obj):
        return obj

    def get_field_value(self, obj, field_name):
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


class ModelNameField(Field):
    """
    Serializes the model instance's model name.  Eg. 'auth.User'.
    """
    def serialize(self, obj):
        return smart_unicode(obj._meta)

    def get_field_value(self, obj, field_name):
        return obj

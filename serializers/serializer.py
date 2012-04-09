from decimal import Decimal
import datetime
import inspect
import types
from serializers.renderers import (JSONRenderer, YAMLRenderer, XMLRenderer)


class Serializer(object):
    class Meta:
        label = None
        include = ()
        exclude = ()
        fields = ()
        include_default_fields = True

    renderer_classes = {
        'xml': XMLRenderer,
        'json': JSONRenderer,
        'yaml': YAMLRenderer
    }

    def __init__(self, include=None, exclude=None, fields=None,
                 include_default_fields=None, label=None, serialize=None):
        if serialize:
            self.serialize = serialize
        self.label = label or getattr(self.Meta, 'label', None)
        self.include = include or getattr(self.Meta, 'include', ())
        self.exclude = exclude or getattr(self.Meta, 'exclude', ())
        self.fields = fields or getattr(self.Meta, 'fields', ())
        self.include_default_fields = (
            include_default_fields or
            getattr(self.Meta, 'include_default_fields', True)
        )

    def is_protected_type(self, obj):
        """
        True if the object is a native datatype that does not need to
        be serialized.
        """
        return isinstance(obj, (
            types.NoneType,
            int, long,
            datetime.datetime, datetime.date, datetime.time,
            float, Decimal,
            basestring)
        )

    def is_simple_callable(self, obj):
        """
        True if the object is a callable that takes no arguments.
        """
        return (
            (inspect.isfunction(obj) and not inspect.getargspec(obj)[0]) or
            (inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1)
        )

    def get_field_serializer_names(self):
        """
        Returns the set of all field names for explicitly declared
        FieldSerializers on this class.
        """
        return  [key for key, val in self.__class__.__dict__.items()
                 if hasattr(val, 'serialize_field_name') and
                    hasattr(val, 'serialize_field_value')]

    def get_field_names(self, obj):
        """
        Given an object, return the set of field names to serialize.
        """
        if self.fields:
            return self.fields
        else:
            include = set(self.include)
            include |= set(self.get_field_serializer_names())
            if self.include_default_fields:
                include |= set(self.get_default_field_names(obj))
            return list(include - set(self.exclude))

    def get_default_field_names(self, obj):
        """
        Given an object, return the default set of field names to serialize.
        This is what would be serialized if no explicit `FieldSerializer`
        are declared, and `include`, `exclude` and `fields` are not set.
        """
        return [key for key in obj.__dict__.keys() if not(key.startswith('_'))]

    def get_field_serializer(self, obj, field_name):
        """
        Given an object and a field name, return the serializer instance that
        should be used to serialize that field.
        """
        try:
            return getattr(self, field_name)
        except AttributeError:
            return self.get_default_field_serializer(obj, field_name)

    def get_default_field_serializer(self, obj, field_name):
        """
        If a field does not have an explicitly declared serializer, return the
        default serializer that should be used for that field.
        """
        return FieldSerializer()

    def serialize_field_name(self, obj, field_name):
        return self.label or field_name

    def serialize_field_value(self, obj, field_name):
        return self.serialize(obj)

    def serialize_object(self, obj):
        ret = {}
        for field_name in self.get_field_names(obj):
            serializer = self.get_field_serializer(obj, field_name)
            key = serializer.serialize_field_name(obj, field_name)
            value = serializer.serialize_field_value(obj, field_name)
            ret[key] = value
        return ret

    def serialize_dict(self, obj):
        return dict([(self.serialize(key), self.serialize(obj[key]))
                      for key in obj.keys()])

    def serialize_iterable(self, obj):
        return [self.serialize(item) for item in obj]

    def serialize_callable(self, obj):
        return self.serialize(obj())

    def serialize(self, obj):
        if self.is_protected_type(obj):
            return obj
        elif hasattr(obj, 'keys'):
            return self.serialize_dict(obj)
        elif hasattr(obj, '__iter__'):
            return self.serialize_iterable(obj)
        elif self.is_simple_callable(obj):
            return self.serialize_callable(obj)
        else:
            return self.serialize_object(obj)

    def encode(self, obj, format=None, **opts):
        data = self.serialize(obj)
        if format:
            return self.render(data, format, **opts)
        return data

    def render(self, data, format, **opts):
        renderer = self.renderer_classes[format]()
        return renderer.render(data, **opts)


class FieldSerializer(Serializer):
    def serialize_field_value(self, obj, field_name):
        return self.serialize(getattr(obj, field_name))


# class ObjectSerializer(Serializer):
#     pass

# class ModelSerializer(Serializer):
#     def get_default_field_names(obj):
#         pass


#     pk = PrimaryKeySerializer()
#     model = ModelNameSerializer()
#     fields = FieldsSerilizer()

#     def serialize



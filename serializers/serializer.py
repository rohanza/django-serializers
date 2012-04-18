from decimal import Decimal
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_str, smart_unicode
import copy
import datetime
import inspect
import types
from serializers.renderers import (JSONRenderer, YAMLRenderer, XMLRenderer)


def _remove_items(seq, exclude):
    """
    Remove duplicates and items in 'exclude' from list (preserving order).
    """
    seen = set()
    result = []
    for item in seq:
        if (item in seen) or (item in exclude):
            continue
        seen.add(item)
        result.append(item)
    return result


def _get_declared_fields(bases, attrs):
    """
    Create a list of serializer field instances from the passed in 'attrs',
    plus any similar fields on the base classes (in 'bases').

    Note that all fields from the base classes are used.
    """
    fields = [(field_name, attrs.pop(field_name))
              for field_name, obj in attrs.items()
              if isinstance(obj, BaseSerializer)]
    fields.sort(key=lambda x: x[1].creation_counter)

    # If this class is subclassing another Serializer, add that Serializer's
    # fields.  Note that we loop over the bases in *reverse*. This is necessary
    # in order to preserve the correct order of fields.
    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields

    return SortedDict(fields)


class SerializerOptions(object):
    def __init__(self, meta, **kwargs):
        self.label = kwargs.get('label', getattr(meta, 'label', None))
        self.source = kwargs.get('source', getattr(meta, 'source', None))
        self.depth = kwargs.get('depth', getattr(meta, 'depth', None))
        self.include = kwargs.get('include', getattr(meta, 'include', ()))
        self.exclude = kwargs.get('exclude', getattr(meta, 'exclude', ()))
        self.fields = kwargs.get('fields', getattr(meta, 'fields', ()))
        self.include_default_fields = kwargs.get('include_default_fields',
            getattr(meta, 'include_default_fields', False)
        )
        self.preserve_field_order = kwargs.get('preserve_field_order',
            getattr(meta, 'preserve_field_order', ())
        )


class SerializerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = _get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class BaseSerializer(object):
    class Meta(object):
        pass

    renderer_classes = {
        'xml': XMLRenderer,
        'json': JSONRenderer,
        'yaml': YAMLRenderer
    }

    creation_counter = 0

    def __init__(self, **kwargs):
        self.opts = SerializerOptions(self.Meta, **kwargs)

        if 'serialize' in kwargs:
            self.serialize = kwargs.get('serialize')

        self.fields = SortedDict((key, copy.copy(field))
                           for key, field in self.base_fields.items())

        self.creation_counter = BaseSerializer.creation_counter
        BaseSerializer.creation_counter += 1

    def initialize(self, parent):
        if parent.opts.depth is not None:
            self.opts.depth = parent.opts.depth - 1

    def _is_protected_type(self, obj):
        """
        True if the object is a native datatype that does not need to
        be serialized further.
        """
        return isinstance(obj, (
            types.NoneType,
            int, long,
            datetime.datetime, datetime.date, datetime.time,
            float, Decimal,
            basestring)
        )

    def _is_simple_callable(self, obj):
        """
        True if the object is a callable that takes no arguments.
        """
        return (
            (inspect.isfunction(obj) and not inspect.getargspec(obj)[0]) or
            (inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1)
        )

    def _serialize_as_string(self, obj):
        return smart_str(obj)

    def get_field_serializer_names(self):
        """
        Returns the set of all field names for explicitly declared
        Serializer fields on this class.
        """
        return self.fields.keys()

    def get_field_names(self, obj):
        """
        Given an object, return the set of field names to serialize.
        """
        opts = self.opts
        if opts.fields:
            return opts.fields
        else:
            fields = self.get_field_serializer_names()
            if opts.include_default_fields or not self.fields:
                fields += self.get_default_field_names(obj)
            fields += list(opts.include)
            return _remove_items(fields, opts.exclude)

    def get_default_field_names(self, obj):
        """
        Given an object, return the default set of field names to serialize.
        This is what would be serialized if no explicit `Serializer` fields
        are declared, and `include`, `exclude` and `fields` are not set.
        """
        return [key for key in obj.__dict__.keys() if not(key.startswith('_'))]

    def get_field_serializer(self, obj, field_name):
        """
        Given an object and a field name, return the serializer instance that
        should be used to serialize that field.
        """
        try:
            return self.fields[field_name]
        except KeyError:
            return self.get_default_field_serializer(obj, field_name)

    def get_default_field_serializer(self, obj, field_name):
        """
        If a field does not have an explicitly declared serializer, return the
        default serializer instance that should be used for that field.
        """
        if self.opts.depth is not None and self.opts.depth <= 0:
            return ValueSerializer()
        return self.__class__()

    def serialize_field_name(self, obj, field_name):
        return self.opts.label or field_name

    def serialize_field_value(self, obj, field_name):
        field_name = self.opts.source or field_name
        if field_name != '*':
            obj = getattr(obj, field_name)
        return self.serialize(obj)

    def serialize_object(self, obj):
        if self.opts.preserve_field_order:
            ret = SortedDict()
        else:
            ret = {}

        for field_name in self.get_field_names(obj):
            serializer = self.get_field_serializer(obj, field_name)
            serializer.initialize(parent=self)
            key = serializer.serialize_field_name(obj, field_name)
            value = serializer.serialize_field_value(obj, field_name)
            ret[key] = value
        return ret

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return self.serialize_object(obj)

    def encode(self, obj, format=None, **opts):
        data = self.serialize(obj)
        if format:
            return self.render(data, format, **opts)
        return data

    def render(self, data, format, **opts):
        renderer = self.renderer_classes[format]()
        return renderer.render(data, **opts)


class Serializer(BaseSerializer):
    __metaclass__ = SerializerMetaclass


class ValueSerializer(Serializer):
    """
    A simple serialzer that leaves primative values as-is, and converts all
    other types to their string representation.
    """

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return smart_unicode(obj)


class ModelSerializer(Serializer):
    """
    A serializer that deals with model instances and querysets.
    """

    def get_default_field_serializer(self, obj, field_name):
        if self.opts.depth is not None and self.opts.depth <= 0:
            return PKSerializer()
        return self.__class__()

    def get_default_field_names(self, obj):
        fields = obj._meta.fields + obj._meta.many_to_many
        return [field.name for field in fields]

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, 'all') and self._is_simple_callable(obj.all):
            return [self.serialize(item) for item in obj.all()]
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return self.serialize_object(obj)


class PKSerializer(Serializer):
    """
    A serializer that returns the model instance's pk value.
    """

    def serialize_object(self, obj):
        return obj.pk


class ModelNameField(Serializer):
    """
    A serializer that returns the model instance's model name.  Eg. 'auth.User'
    """

    def serialize_field_value(self, obj, field_name):
        return smart_unicode(obj._meta)


class DumpDataSerializer(ModelSerializer):
    """
    A serializer that is intended to produce dumpdata formatted structures.
    """

    pk = Serializer()
    model = ModelNameField()
    fields = ModelSerializer(source='*', exclude='id', depth=0)

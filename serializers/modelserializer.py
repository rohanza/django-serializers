from serializer import Serializer
import inspect
import types
import datetime
from decimal import Decimal


class ModelSerializer(Serializer):
    def get_default_field_names(self, obj):
        fields = obj._meta.fields + obj._meta.many_to_many
        return [field.name for field in fields]

    def get_default_field_serializer(self, obj, field_name):
        return ModelSerializerField()


class ModelSerializerField(ModelSerializer):
    def serialize_field_value(self, obj, field_name):
        return self.serialize(getattr(obj, field_name))

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, 'all'):
            return [self.serialize(item) for item in obj.all()]
        return super(ModelSerializerField, self).serialize(obj)

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

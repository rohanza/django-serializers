from serializer import Serializer, BaseFieldSerializer


class ModelSerializer(Serializer):
    def get_default_field_names(self, obj):
        fields = obj._meta.fields + obj._meta.many_to_many
        return [field.name for field in fields]

    def get_default_field_serializer(self, obj, field_name):
        return ModelFieldSerializer()


class ModelFieldSerializer(BaseFieldSerializer, ModelSerializer):
    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, 'all'):
            return [self.serialize(item) for item in obj.all()]
        return super(BaseFieldSerializer, self).serialize(obj)

from serializer import Serializer, FieldSerializer


class ModelSerializer(Serializer):
    def get_default_fields(self, obj):
        return obj._meta.fields + obj._meta.many_to_many

    def get_default_field_names(self, obj):
        return [field.name for field in self.get_default_fields()]


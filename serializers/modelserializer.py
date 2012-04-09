from serializer import Serializer


class ModelSerializer(Serializer):
    def get_default_field_names(self, obj):
        fields = obj._meta.fields + obj._meta.many_to_many
        return [field.name for field in fields]

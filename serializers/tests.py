import datetime
from django.core import serializers
from django.db import models
from django.test import TestCase
from serializers import Serializer, ModelSerializer, DumpDataSerializer
from serializers.fields import Field


class ExampleObject(object):
    """
    An example class for testing basic serialization.
    """
    def __init__(self):
        self.a = 1
        self.b = 'foo'
        self.c = True
        self._hidden = 'other'


class Person(object):
    """
    An example class for testing serilization of properties and methods.
    """
    CHILD_AGE = 16

    def __init__(self, first_name, last_name, age, **kwargs):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        for key, val in kwargs.items():
            setattr(self, key, val)

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def is_child(self):
        return self.age < self.CHILD_AGE

    def __unicode__(self):
        return self.full_name


class EncoderTests(TestCase):
    def setUp(self):
        self.obj = ExampleObject()

    def test_json(self):
        expected = '{"a": 1, "b": "foo", "c": true}'
        output = Serializer().encode(self.obj, 'json', sort_keys=True)
        self.assertEquals(output, expected)

    def test_yaml(self):
        expected = '{a: 1, b: foo, c: true}\n'
        output = Serializer().encode(self.obj, 'yaml')
        self.assertEquals(output, expected)

    def test_xml(self):
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<root><a>1</a><b>foo</b><c>True</c></root>'
        output = Serializer().encode(self.obj, 'xml')
        self.assertEquals(output, expected)


class BasicSerializerTests(TestCase):
    def setUp(self):
        self.obj = ExampleObject()

    def test_serialize_basic_object(self):
        """
        Objects are seriaized by converting into dictionaries.
        """
        expected = {
            'a': 1,
            'b': 'foo',
            'c': True
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)

    def test_serialize_fields(self):
        """
        Setting 'Meta.fields' specifies exactly which fields to serialize.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('a', 'c')

        expected = {
            'a': 1,
            'c': True
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_exclude(self):
        """
        Setting 'Meta.exclude' causes a field to be excluded.
        """
        class CustomSerializer(Serializer):
            class Meta:
                exclude = ('b',)

        expected = {
            'a': 1,
            'c': True
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_include(self):
        """
        Setting 'Meta.include' causes a field to be included.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)

        expected = {
            'a': 1,
            'b': 'foo',
            'c': True,
            '_hidden': 'other'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_include_and_exclude(self):
        """
        Both 'Meta.include' and 'Meta.exclude' may be set.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)
                exclude = ('b',)

        expected = {
            'a': 1,
            'c': True,
            '_hidden': 'other'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_fields_and_include_and_exclude(self):
        """
        'Meta.fields' overrides both 'Meta.include' and 'Meta.exclude' if set.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)
                exclude = ('b',)
                fields = ('a', 'b')

        expected = {
            'a': 1,
            'b': 'foo'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)


class SerializeAttributeTests(TestCase):
    """
    Test covering serialization of different types of attributes on objects.
    """
    def setUp(self):
        self.obj = Person('john', 'doe', 42)

    def test_serialization_only_includes_instance_properties(self):
        """
        By default only serialize instance properties, not class properties.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)

    def test_serialization_can_include_properties(self):
        """
        Object properties can be included as fields.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'full_name': 'john doe',
            'age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialization_can_include_no_arg_methods(self):
        """
        Object methods may be included as fields.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('full_name', 'is_child')

        expected = {
            'full_name': 'john doe',
            'is_child': False
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)


class SerializerFieldTests(TestCase):
    """
    Tests declaring explicit fields on the serializer.
    """

    def setUp(self):
        self.obj = Person('john', 'doe', 42)

    def test_explicit_fields_replace_defaults(self):
        """
        Setting explicit fields on a serializer replaces the default set of
        fields that would have been serialized.
        """
        class CustomSerializer(Serializer):
            full_name = Serializer()

        expected = {
            'full_name': 'john doe',
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_include_default_fields(self):
        """
        If `include_default_fields` is set to `True`, both fields which
        have been explicitly included via a Serializer field declaration,
        and regular default object fields will be included.
        """
        class CustomSerializer(Serializer):
            full_name = Serializer()

            class Meta:
                include_default_fields = True

        expected = {
            'full_name': 'john doe',
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_field_label(self):
        """
        A serializer field can take a 'label' argument, which is used as the
        field key instead of the field's property name.
        """
        class CustomSerializer(Serializer):
            full_name = Serializer(label='Full name')
            age = Serializer(label='Age')

            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'Full name': 'john doe',
            'Age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_field_source(self):
        """
        A serializer field can take a 'source' argument, which is used as the
        field key instead of the field's property name.
        """
        class CustomSerializer(Serializer):
            name = Serializer(source='full_name')
            age = Serializer()

            class Meta:
                fields = ('name', 'age')

        expected = {
            'name': 'john doe',
            'age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_source_all(self):
        """
        Setting source='*', means the complete object will be used when
        serializing that field.
        """
        class CustomSerializer(Serializer):
            full_name = Serializer(label='Full name')
            details = Serializer(fields=('first_name', 'last_name'), label='Details',
                                 source='*')

            class Meta:
                fields = ('full_name', 'details')

        expected = {
            'Full name': 'john doe',
            'Details': {
                'first_name': 'john',
                'last_name': 'doe'
            }
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_source_all_with_custom_serializer(self):
        """
        A custom serializer can be used with source='*' as serialize the
        complete object within a field.
        """
        class DetailsSerializer(Serializer):
            first_name = Serializer(label='First name')
            last_name = Serializer(label='Last name')

            class Meta:
                fields = ('first_name', 'last_name')

        class CustomSerializer(Serializer):
            full_name = Serializer(label='Full name')
            details = DetailsSerializer(label='Details', source='*')

            class Meta:
                fields = ('full_name', 'details')

        expected = {
            'Full name': 'john doe',
            'Details': {
                'First name': 'john',
                'Last name': 'doe'
            }
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_field_func(self):
        """
        A serializer field can take a 'serialize' argument, which is used to
        serialize the field value.
        """
        class CustomSerializer(Serializer):
            full_name = Field(label='Full name',
                              serialize=lambda name: 'Mr ' + name.title())
            age = Serializer(label='Age')

            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'Full name': 'Mr John Doe',
            'Age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    # def test_serializer_fields_do_not_share_state(self):
    #     """
    #     Make sure that different serializer instances do not share the same
    #     SerializerField instances.
    #     """
    #     class CustomSerializer(Serializer):
    #         example = Serializer()

    #     serializer_one = CustomSerializer()
    #     serializer_two = CustomSerializer()
    #     self.assertFalse(serializer_one.fields['example'] is serializer_two.fields['example'])

    def test_serializer_field_order_preserved(self):
        """
        Make sure ordering of serializer fields is preserved.
        """
        class CustomSerializer(Serializer):
            first_name = Field()
            full_name = Field()
            age = Field()
            last_name = Field()

            class Meta:
                preserve_field_order = True

        keys = ['first_name', 'full_name', 'age', 'last_name']

        self.assertEquals(CustomSerializer().serialize(self.obj).keys(), keys)


class NestedSerializationTests(TestCase):
    """
    Tests serialization of nested objects.
    """

    def setUp(self):
        fred = Person('fred', 'bloggs', 41)
        emily = Person('emily', 'doe', 37)
        jane = Person('jane', 'doe', 44, partner=fred)
        self.obj = Person('john', 'doe', 42, siblings=[jane, emily])

    def test_nested_serialization(self):
        """
        Default with nested serializers is to include full serialization of
        child elements.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42,
            'siblings': [
                {
                    'first_name': 'jane',
                    'last_name': 'doe',
                    'age': 44,
                    'partner': {
                        'first_name': 'fred',
                        'last_name': 'bloggs',
                        'age': 41,
                    }
                },
                {
                    'first_name': 'emily',
                    'last_name': 'doe',
                    'age': 37,
                }
            ]
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)

    def test_nested_serialization_with_args(self):
        """
        We can pass serializer options through to nested fields as usual.
        """
        class PersonSerializer(Serializer):
            full_name = Field()
            siblings = Serializer(fields=('full_name',))

        expected = {
            'full_name': 'john doe',
            'siblings': [
                {
                    'full_name': 'jane doe'
                },
                {
                    'full_name': 'emily doe',
                }
            ]
        }

        self.assertEquals(PersonSerializer().serialize(self.obj), expected)

    def test_depth_zero_serialization(self):
        """
        If 'depth' equals 0 then nested objects should be serialized as
        flat values.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42,
            'siblings': [
                'jane doe',
                'emily doe'
            ]
        }

        self.assertEquals(Serializer(depth=0).serialize(self.obj), expected)

    def test_depth_one_serialization(self):
        """
        If 'depth' is greater than 0 then nested objects should be serialized
        as flat values once the specified depth has been reached.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42,
            'siblings': [
                {
                    'first_name': 'jane',
                    'last_name': 'doe',
                    'age': 44,
                    'partner': 'fred bloggs'
                },
                {
                    'first_name': 'emily',
                    'last_name': 'doe',
                    'age': 37,
                }
            ]
        }

        self.assertEquals(Serializer(depth=1).serialize(self.obj), expected)


class RecursiveSerializationTests(TestCase):
    def setUp(self):
        emily = Person('emily', 'doe', 37)
        john = Person('john', 'doe', 42, daughter=emily)
        emily.father = john
        self.obj = john

    def test_recursiive_serialization(self):
        """
        If recursion occurs, serializer will fall back to flat values.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42,
            'daughter': {
                    'first_name': 'emily',
                    'last_name': 'doe',
                    'age': 37,
                    'father': 'john doe'
            }
        }
        self.assertEquals(Serializer().serialize(self.obj), expected)


##### Simple models without relationships. #####

class RaceEntry(models.Model):
    name = models.CharField(max_length=100)
    runner_number = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()


class TestSimpleModel(TestCase):
    def setUp(self):
        self.dumpdata = DumpDataSerializer()
        self.serializer = Serializer(depth=0)
        RaceEntry.objects.create(
            name='John doe',
            runner_number=6014,
            start_time=datetime.datetime(year=2012, month=4, day=30, hour=9),
            finish_time=datetime.datetime(year=2012, month=4, day=30, hour=12, minute=25)
        )

    def test_simple_model(self):
        self.assertEquals(
            self.dumpdata.encode(RaceEntry.objects.all(), 'json'),
            serializers.serialize('json', RaceEntry.objects.all())
        )

    def test_csv(self):
        expected = (
            "finish_time,start_time,id,name,runner_number\r\n"
            "2012-04-30 12:25:00,2012-04-30 09:00:00,1,John doe,6014\r\n"
        )
        self.assertEquals(
            self.serializer.encode(RaceEntry.objects.all(), 'csv'),
            expected
        )


##### One to one relationships #####

class User(models.Model):
    email = models.EmailField()


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    country_of_birth = models.CharField(max_length=100)
    date_of_birth = models.DateTimeField()


class TestOneToOneModel(TestCase):
    """
    Test one-to-one field relationship on a model.
    """
    def setUp(self):
        self.dumpdata = DumpDataSerializer()
        self.nested_model = ModelSerializer()
        self.flat_model = ModelSerializer(depth=0)
        user = User.objects.create(email='joe@example.com')
        Profile.objects.create(
            user=user,
            country_of_birth='UK',
            date_of_birth=datetime.datetime(day=5, month=4, year=1979)
        )

    def test_onetoone_dumpdata_json(self):
        self.assertEquals(
            self.dumpdata.encode(Profile.objects.all(), 'json'),
            serializers.serialize('json', Profile.objects.all())
        )

    def test_onetoone_dumpdata_yaml(self):
        self.assertEquals(
            self.dumpdata.encode(Profile.objects.all(), 'yaml'),
            serializers.serialize('yaml', Profile.objects.all())
        )

    def test_onetoone_nested(self):
        expected = {
            'id': 1,
            'user': {
                'id': 1,
                'email': 'joe@example.com'
            },
            'country_of_birth': 'UK',
            'date_of_birth': datetime.datetime(day=5, month=4, year=1979)
        }
        self.assertEquals(
            self.nested_model.serialize(Profile.objects.get(id=1)),
            expected
        )

    def test_onetoone_flat(self):
        expected = {
            'id': 1,
            'user': 1,
            'country_of_birth': 'UK',
            'date_of_birth': datetime.datetime(day=5, month=4, year=1979)
        }
        self.assertEquals(
            self.flat_model.serialize(Profile.objects.get(id=1)),
            expected
        )


class TestReverseOneToOneModel(TestCase):
    """
    Test reverse relationship of one-to-one fields.

    Note the Django's dumpdata serializer doesn't support reverse relations,
    which wouldn't make sense in that context, so we don't include them in
    the tests.
    """

    def setUp(self):
        self.nested_model = ModelSerializer(include=('profile',))
        self.flat_model = ModelSerializer(depth=0, include=('profile',))
        user = User.objects.create(email='joe@example.com')
        Profile.objects.create(
            user=user,
            country_of_birth='UK',
            date_of_birth=datetime.datetime(day=5, month=4, year=1979)
        )

    def test_reverse_onetoone_nested(self):
        expected = {
            'id': 1,
            'email': u'joe@example.com',
            'profile': {
                'id': 1,
                'country_of_birth': u'UK',
                'date_of_birth': datetime.datetime(day=5, month=4, year=1979),
                'user': 1
            },
        }
        self.assertEquals(
            self.nested_model.serialize(User.objects.get(id=1)),
            expected
        )

    def test_reverse_onetoone_flat(self):
        expected = {
            'id': 1,
            'email': 'joe@example.com',
            'profile': 1,
        }
        self.assertEquals(
            self.flat_model.serialize(User.objects.get(id=1)),
            expected
        )


class Owner(models.Model):
    email = models.EmailField()


class Vehicle(models.Model):
    owner = models.ForeignKey(Owner, related_name='vehicles')
    licence = models.CharField(max_length=20)
    date_of_manufacture = models.DateField()


class TestFKModel(TestCase):
    """
    Test one-to-one field relationship on a model.
    """
    def setUp(self):
        self.dumpdata = DumpDataSerializer()
        self.nested_model = ModelSerializer()
        self.flat_model = ModelSerializer(depth=0)
        self.owner = Owner.objects.create(
            email='tom@example.com'
        )
        self.car = Vehicle.objects.create(
            owner=self.owner,
            licence='DJANGO42',
            date_of_manufacture=datetime.date(day=6, month=6, year=2005)
        )
        self.bike = Vehicle.objects.create(
            owner=self.owner,
            licence='',
            date_of_manufacture=datetime.date(day=8, month=8, year=1990)
        )

    def test_fk_dumpdata_json(self):
        self.assertEquals(
            self.dumpdata.encode(Vehicle.objects.all(), 'json'),
            serializers.serialize('json', Vehicle.objects.all())
        )

    def test_fk_dumpdata_yaml(self):
        self.assertEquals(
            self.dumpdata.encode(Vehicle.objects.all(), 'yaml'),
            serializers.serialize('yaml', Vehicle.objects.all())
        )

    def test_fk_nested(self):
        expected = {
            'id': 1,
            'owner': {
                'id': 1,
                'email': u'tom@example.com'
            },
            'licence': u'DJANGO42',
            'date_of_manufacture': datetime.date(day=6, month=6, year=2005)
        }
        self.assertEquals(
            self.nested_model.serialize(Vehicle.objects.get(id=1)),
            expected
        )

    def test_fk_flat(self):
        expected = {
            'id': 1,
            'owner':  1,
            'licence': u'DJANGO42',
            'date_of_manufacture': datetime.date(day=6, month=6, year=2005)
        }
        self.assertEquals(
            self.flat_model.serialize(Vehicle.objects.get(id=1)),
            expected
        )

    def test_reverse_fk_flat(self):
        expected = {
            'id': 1,
            'email': u'tom@example.com',
            'vehicles':  [1, 2]
        }
        serializer = ModelSerializer(include=('vehicles',), depth=0)
        self.assertEquals(
            serializer.serialize(Owner.objects.get(id=1)),
            expected
        )

    def test_reverse_fk_nested(self):
        expected = {
            'id': 1,
            'email': u'tom@example.com',
            'vehicles': [
                {
                    'id': 1,
                    'licence': u'DJANGO42',
                    'owner': 1,
                    'date_of_manufacture': datetime.date(day=6, month=6, year=2005)
                }, {
                    'id': 2,
                    'licence': u'',
                    'owner': 1,
                    'date_of_manufacture': datetime.date(day=8, month=8, year=1990)
                }
            ]
        }
        serializer = ModelSerializer(include=('vehicles',))
        self.assertEquals(
            serializer.serialize(Owner.objects.get(id=1)),
            expected
        )


class Author(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    authors = models.ManyToManyField(Author, related_name='books')
    title = models.CharField(max_length=100)
    in_stock = models.BooleanField()


class TestManyToManyModel(TestCase):
    """
    Test one-to-one field relationship on a model.
    """
    def setUp(self):
        self.dumpdata = DumpDataSerializer()
        self.nested_model = ModelSerializer()
        self.flat_model = ModelSerializer(depth=0)
        self.lucy = Author.objects.create(
            name='Lucy Black'
        )
        self.mark = Author.objects.create(
            name='Mark Green'
        )
        self.cookbook = Book.objects.create(
            title='Cooking with gas',
            in_stock=True
        )
        self.cookbook.authors = [self.lucy, self.mark]
        self.cookbook.save()

        self.otherbook = Book.objects.create(
            title='Chimera obscura',
            in_stock=False
        )
        self.otherbook.authors = [self.mark]
        self.otherbook.save()

    def test_m2m_dumpdata_json(self):
        self.assertEquals(
            self.dumpdata.encode(Book.objects.all(), 'json'),
            serializers.serialize('json', Book.objects.all())
        )
        self.assertEquals(
            self.dumpdata.encode(Author.objects.all(), 'json'),
            serializers.serialize('json', Author.objects.all())
        )

    def test_m2m_dumpdata_yaml(self):
        self.assertEquals(
            self.dumpdata.encode(Book.objects.all(), 'yaml'),
            serializers.serialize('yaml', Book.objects.all())
        )
        self.assertEquals(
            self.dumpdata.encode(Author.objects.all(), 'yaml'),
            serializers.serialize('yaml', Author.objects.all())
        )

    def test_m2m_nested(self):
        expected = {
            'id': 1,
            'title': u'Cooking with gas',
            'in_stock': True,
            'authors': [
                {'id': 1, 'name': 'Lucy Black'},
                {'id': 2, 'name': 'Mark Green'}
            ]
        }
        self.assertEquals(
            self.nested_model.serialize(Book.objects.get(id=1)),
            expected
        )

    def test_m2m_flat(self):
        expected = {
            'id': 1,
            'title': u'Cooking with gas',
            'in_stock': True,
            'authors': [1, 2]
        }
        self.assertEquals(
            self.flat_model.serialize(Book.objects.get(id=1)),
            expected
        )

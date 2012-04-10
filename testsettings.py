DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'database.sql',
    },
}

INSTALLED_APPS = (
    'serializers',
    'django.contrib.auth',
    'django.contrib.contenttypes'
)

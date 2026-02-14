# Goals:
- Create djang project with webapp and api app.
- Interact with postgres server or mongo server
- Create a trainining webapp to preview sdsai engine.
- Every project or application will have entry point, so, what is django ENTRYPOINT?
    - Answer: each project app will have "urls" to serve requests. django core handle listen request and parse to correspondent app based on their prefix (admin/ or web/ or api/)
- Which ORM django works with?
- Which pattern django works with?
    - Model View Template (MVT)

# Basics:
- https://www.geeksforgeeks.org/django-basics/

## Installations
 ```pip3 install django``` will install everything related to django with tool ```django-admin```
 ```django-admin``` to view all commands

## Django core commands
- ```django-admin``` will call command in django core library
- ```django-admin startproject```: create a new project with django with structure projectname/projectname.
    - django-admin startproject sds will create 
        - sds: project root
            sds: main application contains project settings        
            manage.py: management file in django. 
- **** NOTE: for a clearer structure, we can move sub project name to be a top project.
- ```django-admin startapp```: create new application in current project root. 
    - Run ```django-admin startapp api```
    - Run ```python manage.py startapp api``` will be same in mainapp [sds] because it will call django core to run commands with some <bold>extra<bold> commands for application. 
    - Go to project mainapp ([sds]) and run ```python manage.py``` to view core commands (same as djang-admin) and extra command.
    - Run go to directory [sds] and run both command 
        - ```django-admin startapp test1```
        - ```python manage.py startapp test2```
        - Finally, command those directories [test1] and [test2]
        - Reference: https://www.geeksforgeeks.org/how-to-create-an-app-in-django/?ref=lbp

- makemigrations: create migration when a model changed.
- showmigration: show migration scripts will be run 
- runserver: start a server to run app.

## Django contribution packages:
- Django provide a lot of contrib packages (admin, auth, contenttypes).
- These packages can be understood as "middlewares" in nestjs
- So, right after created your app, you need to "install" your app in settings.py
```
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "your_app_name" (web)
    ]
```
## Django project structure:
- Reference links: https://www.geeksforgeeks.org/django-project-mvt-structure/
- project name
    - project app (2 important module settings and urls)
        - settings.py
        - urls.py: django server will listen request and parse url and redirect to your url.
            - so that, we need to specify your path in urls.py such as ```path('api', api.urls)```
    - your_app_1
    - your_app_2

## Create new django application: 
- A django application is independant (WIP)
- ROOT_URLCONF = "sds.urls"

## Django urls and url_patterns:
- Read admin.site.urls
- The url that django core read will "url_patterns"

# ORM
https://www.geeksforgeeks.org/django-tutorial/?ref=lbp
https://www.pythontutorial.net/django-tutorial/django-one-to-one/
https://testdriven.io/blog/django-and-pydantic/

# Django serializers:
## Solution 1: 
- Create a dto to get json data from model. because django.core.serializers will return {'model' : 'web.Location', 'pk': 1, fieds: { 'name' : 'test' }} => we don't need "model" and "pk" fields

## Solution 2:
- Use django.core.serializers but then keep "fields" property only. This is not good performance.

## Solution 3:
- Use djangorestframework.
- First, create a ModelSerializer with class Meta is (model, fields....)
- Second, create serializer and serialize the data from queryset.

# What is generic in Python and how to use:
- REMEMBER: Python is a intepreter language. So GeneralSerializer.Meta.model equals Meta is static property of GenerialSerializer
- model = self.kwargs.get('model') => get from keyword argument key 'model'. And by default, key 'model' = Location or Organization. -> reflection
```
from rest_framework import viewsets

class GenericViewSet(viewsets.ModelViewSet):

     def get_queryset(self):
         model = self.kwargs.get('model')
         return model.objects.all()           

     def get_serializer_class(self):
         GeneralSerializer.Meta.model = self.kwargs.get('model')
```
- But, this is not thread-safe, only apply in http request only because when running in mulitple threadings, the static class GeneralSerializer will be changed frequently and subclass Metal with "model" will be changed too.

# Good links:
- Override ModelViewSet: https://stackoverflow.com/questions/61695267/how-do-i-override-viewsets-modelviewset-in-django-rest-framework
- How to remove trailing_plash in restframework:
    - Disable trailing_plash in SimpleRouter => ```router = routers.SimpleRouter(trailing_slash=False)```
- How to add pagination: https://djangosnippets.org/snippets/10717/
- Nested path https://studygyaan.com/django/nested-routers-in-django-rest-framework

# APIView vs ModelViewSets
- https://stackoverflow.com/questions/25125959/django-rest-framework-generics-or-modelviewsets
- https://github.com/alanjds/drf-nested-routers

# How to apply DTO to Model in Django

## Solution 1:
- Create a ```CreateLocationDTO(models.Model)``` with property as ```Location`` and then, we will create a serilizer for that.
- Usecase: when user has different data as mode.
    - Location: (na)
    - CreateLocationDTO: (name, parentID)
- Pros & cons: Unable to re-use ```serializer.save()``` because ```serializer works with model in database```

## Solution 2:
- Create a serializer for each case. For example, we can create ```CreateLocationSerializer``` if method is ```POST```
- Usecase: when user has same data as model

# How to create custom middleware:
- Create a class ResponseMiddleware with MiddlewareMixin
    - Override process_request
    - Override process_response
- Reference with (path)[venv/lib/python3.9/site-packages/django/utils/deprecation.py]

# How to use custom command: 
- Create a new app (startapp): commands
    - Create a management sub dir
    - Create a commands subdir
    - Add a command name "mostused.py"

# How to use celery with beat and worker
## beat scheduler
- Config ```app.conf.beat_schedule``` or CELERY_BEAT_SCHEDULE 
- Run ```python -m celery -A sds beat``` to run all beat schedulers
## worker
- Celery will auto discover all tasks that can consume a queue.
- Run ```python -m celery -A sds worker -Q sdspdf.publish_sdspdf``` to create consumer for queue ```sdspdf.publish_sdspdf```. At this time, celery will listen queue and create appropriate task (task in header of payload).
## Issues:
- Issue 01: Did you remember to import the module containing this task?
Or maybe you're using relative imports?
- Issue 02: Stuck to publish messages to exchange
### Fix:
- Project web has tasks.py
- Project integration has "dir" tasks only.
- Celery autodiscover will discovery in each installed app with related_name = "tasks". 
- At this time, Celery call _autodiscover_tasks_from_fixups -> _autodiscover_tasks_from_names with packages from INSTALLED_APPS (settings).
- Finally, it will search find_related_module. 
    - In web, tasks.py is a module.
    - In integrations, tasks is a folder with test.py module so that in __init__.py, we need to import that module for integrations. This adding results find_related_module can search tasks
- Issue 03 - But, when move tasks into files and into "tasks" folder, the models or services will be loaded before task and raise ```django.core.exceptions.AppRegistryNotReady```. Temp, I will use tasks.py for integrations. This is because some models are not loaded. How to fix? 


# Elasticsearch:
- From version > 8.0.0, elasticsearch provide cloud version only.
```pip install "elasticsearch-dsl>=7.0.0,<8.0.0" django-elasticsearch-dsl```

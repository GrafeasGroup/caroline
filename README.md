# caroline

[![Build Status](https://travis-ci.org/GrafeasGroup/caroline.svg?branch=master)](https://travis-ci.org/GrafeasGroup/caroline)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/84632bae1d3f4dd8ad69cf90fd0a8d6b)](https://www.codacy.com/app/joe-kaufeld/caroline?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=GrafeasGroup/caroline&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/84632bae1d3f4dd8ad69cf90fd0a8d6b)](https://www.codacy.com/app/joe-kaufeld/charlotte?utm_source=github.com&utm_medium=referral&utm_content=GrafeasGroup/caroline&utm_campaign=Badge_Coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Packaged with Poetry](https://img.shields.io/badge/packaged%20with-poetry-blue.svg)](https://poetry.eustace.io)

A key-value JSON ODM with a memorable name.

### What is caroline?
Caroline is yet another way to store JSON data. It contains backends for Elasticsearch and Redis, and allows you to use both in the same project! Included in the box (and heavily recommended that you use) is jsonschema support.


### Why?
The existing options that are available didn't quite work for what we were looking for, so we wrote our own for internal use and decided to open source it. The goal of the project is easy integration without high overhead.

### How does it work?

The only thing you need to do to get started is `from caroline import Prototype`. Then you can start building your data classes:

```python
from caroline import Prototype

class Dog(Prototype):
    default = {
        "breed": "",
        "age": 1,
        "name": ""
    }
    schema = {
        "type": "object",
        "properties": {
            "breed": {
                "type": "string"
            },
            "age": {
                "type": "number"
            },
            "name": {
                "type": "string"
            }
        }
    }
    
sam = Dog('sam')

print(sam)
# >>> {"breed": "", "age": 1, "name": ""}

sam.update('name', 'Sam')
# OR
sam['name'] = 'Sam'

sam.update('age', 5)
sam.update('breed', 'mutt')
sam.save()
```
When you create a new instance of your class with an ID (like `Dog('sam')`), that's the key that the particular record will be saved under. That means that if you create a class with that name, it'll load the same record again:

```python
from example_above import Dog

x = Dog('sam')

print(x)
# >>> {'breed': 'mutt', 'age': 5, 'name': 'Sam'}
```
If you create an instance of your class with an ID that isn't in your chosen database, then it will instantiate it using the `default` dict that you defined in the class. 

caroline will automatically handle its own connections, but if you've got a custom one, feel free to pass it in through your model:

```python
class Cat(Prototype):
    elasticsearch_conn = your_elasticsearch_connection
    # OR
    redis_conn = your_redis_connection
    
    default = {}
```
NOTE: You cannot have more than one connection on your model! Each model can only work with one database; that being said, you _can_ have each model route to a different database if you want to and caroline with handle it for you. If you don't want to pass a specific connection with each model, we don't blame you; The default connection is Elasticsearch, but you can change that by setting the environment variable `CAROLINE_DEFAULT_DB` to either "elasticsearch" or "redis". You can also import the caroline config directly and manually set the requested database as the default (`caroline.config.default_db = "redis"`).

There is currently not a way to change the ElasticSearch location, but you can set the Redis location by formatting your Redis address as a URL, (e.g. `redis://localhost:6379/0`) which caroline will pick up if you set it as the environment variable `CAROLINE_REDIS_URL`.

If time goes on and you need to upgrade your models, we have a plan for that! Just modify your model (add new fields or remove them), then load your keys as normal. Call `.upgrade()` on the object that you've retrieved from the database and caroline will force your existing data into the new model. THIS IS A DESTRUCTIVE CALL.

```python
from caroline import Prototype

class Dog(Prototype):
    default = {
        "age": 1,
        "name": "",
        "sire": "",
        "dam": ""
    }
    db = 'redis'

x = Dog('sam')
print(x)

# we get the last time we used the key `sam` for the prototype class `Dog`
# >>> {'breed': 'mutt', 'age': 5, 'name': 'Sam'}

# THIS CALL RESULTS IN THE DESTRUCTION OF DATA
x.upgrade()
print(x)

# >>> {'age': 5, 'name': 'Sam', 'sire': '', 'dam': ''}
x.save()
```

caroline also gives you the ability to choose your database root key names; by default, it will be the name of the class model you create. So for example, if you have a class named Dog with the record ID of 'sam' from above, then the record in the DB will have the key of `::dog::sam`. You can adjust the first part by adding another parameter: `db_key`. Don't bother with this unless you have a good reason to change it.

A note on schemas: while we provide support for jsonschema (and that was the driving force behind the creation of this package), you don't have to use it -- as the above example illustrates, you don't need to create a `schema` key. If no `schema` is passed in, it does not perform the validation step on `.save()` -- otherwise, it validates the data against the schema every time `.save()` is called.

Finally, sometimes you just need a dict; our prototype classes do a great job of pretending to be a dict, but if you ever actually just need the data, call `.to_dict()` and a regular dictionary will be returned.

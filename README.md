# charlotte

[![Build Status](https://travis-ci.org/GrafeasGroup/charlotte.svg?branch=master)](https://travis-ci.org/GrafeasGroup/charlotte)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/84632bae1d3f4dd8ad69cf90fd0a8d6b)](https://www.codacy.com/app/joe-kaufeld/charlotte?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=GrafeasGroup/charlotte&amp;utm_campaign=Badge_Grade)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

A Redis-based JSON ODM with a memorable name.

### What is charlotte?
Charlotte is yet another way to store JSON data in Redis. Included in the box (and heavily recommended that you use) is jsonschema support.


### Why?
The existing options that are available didn't quite work for what we were looking for, so we wrote our own for internal use and decided to open source it. The goal of the project is easy integration without high overhead.

### How does it work?

The only thing you need to do to get started is `from charlotte import Prototype`. Then you can start building your data classes:

```python
from charlotte import Prototype

class Dog(Prototype):
    default_structure = {
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
# {'breed': 'mutt', 'age': 5, 'name': 'Sam'}
```
Charlotte will automatically handle its own Redis connections, but if you've got a custom one, feel free to pass it in through your model:

```python
class Cat(Prototype):
    redis_conn = your_redis_connection
    default_structure = {}
```
Charlotte also gives you the ability to choose your database root key names; by default, it will be the name of the class model you create. So for example, if you have a class named Dog with the record ID of 'sam' from above, then the record in the DB will have the key of `::dog::sam`. You can adjust the first part by adding another parameter: `db_key`. Don't bother with this unless you have a good reason to change it.

A note on schemas: while we provide support for jsonschema (and that was the driving force behind the creation of this package), you don't have to use it -- as the above example illustrates, you don't need to create a `schema` key. If no `schema` is passed in, it does not perform the validation step on `.save()` -- otherwise, it validates the data against the schema every time `.save()` is called.

Finally, sometimes you just need a dict; our prototype classes do a great job of pretending to be a dict, but if you ever actually just need the data, call `.to_dict()` and a regular dictionary will be returned.

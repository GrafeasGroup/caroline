#!/usr/bin/env python

import os
import sys
import codecs
import re
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    # noinspection PyAttributeOutsideInit
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, 'cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def long_description():
    if not (os.path.isfile("README.md") and os.access("README.md", os.R_OK)):
        return ""

    with codecs.open("README.md", encoding="utf8") as f:
        return f.read()


testing_deps = ["pytest", "pytest-cov"]
dev_helper_deps = ["black"]

REQUIRED = [
    "redis",
    "jsonschema",
    "elasticsearch",
    "addict",
]

# What packages are optional?
EXTRAS = {
    "dev": testing_deps + dev_helper_deps
}

setup(
    name="charlotte",
    version="0.4.0",
    description="A key/value-based JSON ODM with a memorable name.",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/GrafeasGroup/charlotte",
    author="Grafeas Group, Ltd.",
    author_email="devs@grafeas.org",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Database :: Front-Ends",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="",
    packages=find_packages(exclude=["test", "test.*", "*.test", "*.test.*"]),
    zip_safe=True,
    cmdclass={"test": PyTest},
    test_suite="test",
    extras_require=EXTRAS,
    setup_requires=[],
    tests_require=testing_deps,
    install_requires=REQUIRED,
)

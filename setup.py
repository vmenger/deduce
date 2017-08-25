
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
# from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='deduce',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='1.0.0',

    description="Deduce: de-identification method for Dutch medical text",

    # The project's main homepage.
    url='https://github.com/vmenger/deduce/',

    # Author details
    author='Vincent Menger',
    author_email='v.j.menger@uu.nl',

    packages=['deduce'],

    # Data files
    package_data={'deduce': ['data/*']},

    # Choose your license
    license='GNU GPLv3',

    # What does your project relate to?
    keywords='de-identification',

    install_requires=['nltk'],
)

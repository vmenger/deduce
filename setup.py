from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

version = {}
with open(path.join(here, 'deduce', '__version__.py')) as fp:
    exec(fp.read(), version)

setup(
    name='deduce',

    version=version['__version__'],

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

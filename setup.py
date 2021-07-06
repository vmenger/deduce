from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

version = {}
with open(path.join(here, 'deduce', '__version__.py')) as fp:
    exec(fp.read(), version)

with open("README.md", "r") as fh:
    readme = fh.read()

setup(
    name='deduce',

    version=version['__version__'],

    description='Deduce: de-identification method for Dutch medical text',
    long_description=readme,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    url='https://github.com/vmenger/deduce/',

    # Author details
    author='Vincent Menger',
    author_email='vmenger@protonmail.com',

    packages=['deduce'],

    # Data files
    package_data={'deduce': ['data/*']},

    # Choose your license
    license='GNU LGPLv3',

    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='de-identification',

    install_requires=['nltk'],
)

format:
	python -m black .
	python -m isort .
	python -m docformatter .

lint:
	python -m flake8 .
	python -m pylint deduce/

build-docs:
	sphinx-apidoc --module-first --force --templatedir=docs/templates -o docs/source/api deduce
	sphinx-build docs/source docs/_build/html -c docs/
	python docs/emojize.py docs/_build/html

clean:
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf docs/_build
	rm -rf docs/source/api

.PHONY: format lint clean

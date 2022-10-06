test:
	python -m unittest discover -s ./tests/unittests  -p 'test_*.py'

format:
	isort deduce/ --profile black
	python -m black --line-length 120 deduce/
	pylint --max-line-length=120 deduce/


publish:
	pip install --upgrade setuptools wheel twine
	python setup.py sdist bdist_wheel
	twine upload  dist/*
	rm -fr build dist .egg deduce.egg-info


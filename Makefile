test:
	python -m unittest discover

format:
	python -m black deduce/
	pylint --max-line-length=140 deduce/


publish:
	pip install --upgrade setuptools wheel twine
	python setup.py sdist bdist_wheel
	twine upload  dist/*
	rm -fr build dist .egg deduce.egg-info


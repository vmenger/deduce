test:
	python -m pytest --cov-report html --cov=deduce tests/


format:
	python -m isort deduce/ tests/ --profile black
	python -m black --line-length 120 deduce/ tests/
	python -m flake8 --select ANN001,ANN2,ANN3 deduce/
	python -m pylint --max-line-length=120 --disable=C0114 deduce/


publish:
	pip install --upgrade setuptools wheel twine
	python setup.py sdist bdist_wheel
	twine upload  dist/*
	rm -fr build dist .egg deduce.egg-info


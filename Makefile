MAX_LINE_LENGTH := 120
CHECK ?= 0

format_dirs := deduce/ tests/
lint_dirs := deduce/

black_args := --line-length $(MAX_LINE_LENGTH)
isort_args := --profile black
typehints_args := --select ANN001,ANN2,ANN3 --max-line-length $(MAX_LINE_LENGTH)
pylint_args := --disable=C0114 --max-line-length=$(MAX_LINE_LENGTH)

ifeq ($(CHECK), 1)
	black_args += --check
	isort_args += -c
	pylint_args += --fail-under 9.0

else
	typehints_args += --exit-zero
	pylint_args += --exit-zero
endif

format: black isort

lint: typehints pylint

black:
	python -m black $(black_args) $(format_dirs)

isort:
	python -m isort $(isort_args)  $(format_dirs)

typehints:
	python -m flake8 $(typehints_args) $(lint_dirs)

pylint:
	python -m pylint $(pylint_args) $(lint_dirs)

test:
	python -m pytest --cov-report html --cov=deduce tests/

clean:
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .pytest_cache

.PHONY: format lint black isort typehints pylint test clean
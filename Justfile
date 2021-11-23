doc:
    cd docs && poetry run make html

cleandoc:
    cd docs && poetry run make clean

test: unittest functest

lf:
    poetry run pytest -sxvvv --lf

unittest:
    poetry run pytest -sxv tests/unittests

functest:
    poetry run pytest -sxv tests/functionals

black:
    poetry run black **/*.py

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

coverage:
    poetry run pytest tests/unittests --cov-report=html --cov=aioli
    xdg-open htmlcov/index.html

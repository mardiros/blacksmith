default_test_suite := 'tests/unittests'

doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && poetry run make clean

test: unittest functest

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

functest:
    poetry run pytest -sxv tests/functionals

black:
    poetry run isort .
    poetry run black .

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=aioli {{test_suite}}
    xdg-open htmlcov/index.html

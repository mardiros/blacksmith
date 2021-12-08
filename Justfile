doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

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
    poetry run isort .
    poetry run black .

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

coverage:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest tests/unittests --cov-report=html --cov=aioli
    xdg-open htmlcov/index.html

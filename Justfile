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

rdt:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

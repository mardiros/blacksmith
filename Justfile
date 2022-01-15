default_test_suite := 'tests/unittests'

doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && poetry run make clean

gensync:
    poetry run python scripts/gen_unasync.py
    poetry run isort src/blacksmith/middleware/_sync
    poetry run black src/blacksmith/middleware/_sync
    poetry run isort src/blacksmith/sd/_sync
    poetry run black src/blacksmith/sd/_sync
    poetry run isort src/blacksmith/service/_sync
    poetry run black src/blacksmith/service/_sync
    poetry run isort tests/unittests/_sync
    poetry run black tests/unittests/_sync

test: unittest functest lint

lf:
    poetry run pytest -sxvvv --lf

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

functest:
    poetry run pytest -sxv tests/functionals

lint:
    poetry run flake8

black:
    poetry run isort .
    poetry run black .

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

mypy:
    poetry run mypy src/blacksmith/

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=blacksmith {{test_suite}}
    xdg-open htmlcov/index.html

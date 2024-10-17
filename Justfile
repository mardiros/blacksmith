package := 'blacksmith'
default_test_suite := 'tests/unittests'

install:
    poetry install --with dev

doc:
    cd docs && poetry run make html
    xdg-open docs/build/html/index.html

cleandoc:
    cd docs && poetry run make clean

gensync:  && fmt
    poetry run python scripts/gen_unasync.py

lint:
    poetry run ruff check .

test: lint mypy unittest functest

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lf:
    poetry run pytest -sxvvv --lf

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov={{package}} {{test_suite}}
    xdg-open htmlcov/index.html

functest:
    poetry run pytest -sxv tests/functionals

mypy:
    poetry run mypy src/ tests/

fmt:
    poetry run ruff check --fix .
    poetry run ruff format src tests

gh-pages:
    poetry export --with dev -f requirements.txt -o docs/requirements.txt --without-hashes

release major_minor_patch: gensync test gh-pages && changelog
    poetry version {{major_minor_patch}}
    poetry install

changelog:
    poetry run python scripts/write_changelog.py
    cat CHANGELOG.rst >> CHANGELOG.rst.new
    rm CHANGELOG.rst
    mv CHANGELOG.rst.new CHANGELOG.rst
    $EDITOR CHANGELOG.rst

publish:
    git commit -am "Release $(poetry version -s)"
    poetry build
    poetry publish
    git push
    git tag "$(poetry version -s)"
    git push origin "$(poetry version -s)"

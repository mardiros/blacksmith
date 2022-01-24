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

lint:
    poetry run flake8 && echo "$(tput setaf 10)Success: no lint issue$(tput setaf 7)"

test: lint mypy unittest functest

unittest test_suite=default_test_suite:
    poetry run pytest -sxv {{test_suite}}

lf:
    poetry run pytest -sxvvv --lf

cov test_suite=default_test_suite:
    rm -f .coverage
    rm -rf htmlcov
    poetry run pytest --cov-report=html --cov=blacksmith {{test_suite}}
    xdg-open htmlcov/index.html

functest:
    poetry run pytest -sxv tests/functionals

mypy:
    poetry run mypy src/ tests/

black:
    poetry run isort .
    poetry run black .

rtd:
    poetry export --dev -f requirements.txt -o docs/requirements.txt

release major_minor_patch: gensync test rtd && changelog
    poetry version {{major_minor_patch}}
    poetry install

changelog:
    poetry run python scripts/write_changelog.py
    cat CHANGELOG.rst >> CHANGELOG.rst.new
    rm CHANGELOG.rst
    mv CHANGELOG.rst.new CHANGELOG.rst
    $EDITOR CHANGELOG.rst

publish:
    git commit -am "Release $(poetry run python scripts/show_release.py)"
    poetry build
    poetry publish
    git push
    git tag "$(poetry run python scripts/show_release.py)"
    git push origin "$(poetry run python scripts/show_release.py)"

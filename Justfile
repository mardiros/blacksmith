doc:
    cd docs && poetry run make html

test: unittests functionaltests

unittests:
    poetry run pytest -sxv tests/unittests

functionaltests:
    poetry run pytest -sxv tests/functionals

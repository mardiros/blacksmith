doc:
    cd docs && poetry run make html

cleandoc:
    cd docs && poetry run make clean

test: unittests functionaltests

unittests:
    poetry run pytest -sxv tests/unittests

functionaltests:
    poetry run pytest -sxv tests/functionals

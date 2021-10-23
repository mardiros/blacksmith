doc:
    cd docs && poetry run make html

test:
    poetry run pytest -sxv

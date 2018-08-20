#!/bin/sh

set -e

flake8 .
black --check --diff .
isort --recursive --check-only .

if [ $1 = "postgres" ];
then
    pytest test --verbose --cov --postgres
else
    pytest test --verbose --cov
fi
sphinx-build docs/ docs/_build -W
python setup.py sdist
python setup.py bdist_wheel

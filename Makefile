.PHONY: test pytest build-dev
default: run-tests

test: build-dev
	pipenv run py.test -vv --cov=karp --cov-report=term-missing tests > pytest.log

run-tests: lint type-check test
tox:
	tox

build: Pipfile
	pipenv install

build-dev: .venv/build-dev
.venv/build-dev: Pipfile
	pipenv install --dev
	touch $@

lint:
	flake8 src tests setup.py wsgi.py

type-check:
	pyre check

run-dev:
	pipenv run python wsgi.py

prepare-release:
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev > requirements-dev.txt

docs/openapi.html: doc/karp_api_spec.yaml
	redoc-cli bundle --output $@ $<

bumpversion-patch:
	bumpversion patch

bumpversion-minor:
	bumpversion minor

bumpversion-major:
	bumpversion major

mkrelease-patch: bumpversion-patch prepare-release docs/openapi.html
mkrelease-minor: bumpversion-minor prepare-release docs/openapi.html
mkrelease-major: bumpversion-major prepare-release docs/openapi.html

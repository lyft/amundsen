IMAGE := amundsendev/amundsen-search
VERSION:= $(shell grep -m 1 '__version__' setup.py | cut -d '=' -f 2 | tr -d "'" | tr -d '[:space:]')

.PHONY: test
clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf dist/

.PHONY: test_unit
test_unit:
	python3 -bb -m pytest tests

.PHONY: lint
lint:
	flake8 .

.PHONY: mypy
mypy:
	mypy --ignore-missing-imports --strict-optional --warn-no-return .

.PHONY: isort
isort:
	isort .

.PHONY: isort_check
isort_check:
	isort ./ --check --diff

.PHONY: test
test: test_unit lint mypy isort_check

.PHONY: image
image:
	cd .. && docker build -f Dockerfile.search.public -t ${IMAGE}:latest . && cd search

.PHONY: image-version
image-version:
	cd .. && docker build -f Dockerfile.search.public -t ${IMAGE}:${VERSION} . && cd search

.PHONY: push-image-version
push-image-version:
	docker push ${IMAGE}:${VERSION}

.PHONY: push-image
push-image:
	docker push ${IMAGE}:latest

.PHONY: build-push-image
build-push-image-latest: image push-image
build-push-image-version: image-version push-image-version

.PHONY: install_deps
install_deps:
	pip3 install -e ".[all]"

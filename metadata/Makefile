IMAGE := amundsendev/amundsen-metadata
OIDC_IMAGE := ${IMAGE}-oidc
VERSION:= $(shell grep -m 1 '__version__' setup.py | cut -d '=' -f 2 | tr -d "'" | tr -d '[:space:]')

.PHONY: clean
clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf dist/

.PHONY: test_unit
test_unit:
	python3 -b -m pytest tests

lint:
	python3 -m flake8

.PHONY: mypy
mypy:
	mypy --ignore-missing-imports --follow-imports=skip --strict-optional --warn-no-return .

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
	cd .. && docker build -f Dockerfile.metadata.public -t ${IMAGE}:latest . && cd metadata

.PHONY: image-version
image-version:
	cd .. && docker build -f Dockerfile.metadata.public -t ${IMAGE}:${VERSION} . && cd metadata

.PHONY: push-image-version
push-image-version:
	docker push ${IMAGE}:${VERSION}

.PHONY: push-image
push-image:
	docker push ${IMAGE}:latest

.PHONY: oidc-image
oidc-image:
	cd .. && docker build -f Dockerfile.metadata.public --target=oidc-release -t ${OIDC_IMAGE}:${VERSION} . && cd metadata
	docker tag ${OIDC_IMAGE}:${VERSION} ${OIDC_IMAGE}:latest

.PHONY: push-odic-image
push-oidc-image:
	docker push ${OIDC_IMAGE}:${VERSION}
	docker push ${OIDC_IMAGE}:latest



.PHONY: build-push-image
build-push-image-latest: image oidc-image push-image push-oidc-image
build-push-image-version: image-version push-image-version

.PHONY: install_deps
install_deps:
	pip3 install -e ".[all]"

IMAGE := amundsendev/amundsen-frontend
OIDC_IMAGE := ${IMAGE}-oidc
VERSION:= $(shell grep -m 1 '__version__' setup.py | cut -d '=' -f 2 | tr -d "'" | tr -d '[:space:]')

.PHONY: clean
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
	mypy --ignore-missing-imports --follow-imports=skip --strict-optional --warn-no-return .

.PHONY: test
test: test_unit lint mypy

.PHONY: image
image:
	cd .. && docker build -f Dockerfile.frontend.public -t ${IMAGE}:latest . && cd frontend

.PHONY: image-version
image-version:
	cd .. && docker build -f Dockerfile.frontend.public -t ${IMAGE}:${VERSION} . && cd frontend

.PHONY: push-image-version
push-image-version:
	docker push ${IMAGE}:${VERSION}

.PHONY: push-image
push-image:
	docker push ${IMAGE}:latest

.PHONY: oidc-image
oidc-image:
	cd .. && docker build -f Dockerfile.frontend.public --target=oidc-release -t ${OIDC_IMAGE}:${VERSION} . && cd frontend
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

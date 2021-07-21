clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf dist/

.PHONY: test_unit
test_unit:
	python3 -bb -m pytest tests

lint:
	flake8 .

.PHONY: mypy
mypy:
	mypy .

.PHONY: isort
isort:
	isort .

.PHONY: isort_check
isort_check:
	isort ./ --check --diff

.PHONY: test
test: test_unit lint mypy isort_check

.PHONY: install_deps
install_deps:
	pip3 install -e ".[all]"

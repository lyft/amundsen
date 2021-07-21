clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf dist/

test_unit:
	python -m pytest tests
	python3 -bb -m pytest tests


lint:
	flake8 .

.PHONY: mypy
mypy:
	mypy .


test: test_unit lint mypy

.PHONY: install_deps
install_deps:
	pip3 install -e ".[all]"

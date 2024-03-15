install:
	python -m pip install --upgrade pip && \
	python -m pip install -e .[dev]

test:
	black --check redbrick && \
	flake8 --benchmark --count redbrick && \
	pycodestyle --benchmark --count --statistics redbrick && \
	pydocstyle --count redbrick && \
	mypy redbrick && \
	pylint --rcfile=setup.cfg -j=3 --recursive=y redbrick && \
	pytest -n 0 tests

build: install
	python -m build -w -n

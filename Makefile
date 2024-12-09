clean:
	rm -rf redbrick_sdk*.egg-info redbrick_sdk*.whl

install:
	python -m pip install --upgrade pip && \
	python -m pip install -e .[dev]

lint:
	black --check redbrick && \
	flake8 --benchmark --count redbrick && \
	pycodestyle --benchmark --count --statistics redbrick && \
	pydocstyle --count redbrick && \
	mypy redbrick && \
	pylint --rcfile=setup.cfg -j=3 --recursive=y redbrick

unit:
	pytest -n 0 tests

test: lint unit

build: clean install
	python -m build -w -n -o .

docker: build
	docker build -t redbrickai/redbrick-sdk:latest -t redbrickai/redbrick-sdk:`python -c 'import redbrick;print(redbrick.__version__)'` .

test:
	black --check redbrick && \
	flake8 --benchmark --count redbrick && \
	pycodestyle --benchmark --count --statistics redbrick && \
	pycodestyle --count redbrick && \
	mypy redbrick && \
	pylint --rcfile=setup.cfg -j=3 --recursive=y redbrick && \
	pytest -n 0 tests

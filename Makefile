test:
	./.venv/bin/black --check redbrick && \
	./.venv/bin/flake8 --benchmark --count redbrick && \
	./.venv/bin/pycodestyle --benchmark --count --statistics redbrick && \
	./.venv/bin/pycodestyle --count redbrick && \
	./.venv/bin/mypy redbrick && \
	./.venv/bin/pylint --rcfile=setup.cfg -j=3 --recursive=y redbrick && \
	./.venv/bin/pytest -n 0 tests

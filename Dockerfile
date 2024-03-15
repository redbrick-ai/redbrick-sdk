FROM python:3.12-slim
WORKDIR /usr/src/app

ENV VIRTUAL_ENV="/usr/src/lib/.venv" PATH="/usr/src/lib/.venv/bin:$PATH" REDBRICK_DISABLE_VERSION_CHECK="1"
RUN python -m venv /usr/src/lib/.venv && pip install --upgrade pip

COPY dist/*.whl ./
RUN pip install *.whl && rm *.whl

CMD ["python", "-i", "-c", "import redbrick"]

FROM python:3.12-slim
WORKDIR /usr/src/lib

ENV VIRTUAL_ENV="/usr/src/lib/.venv" PATH="/usr/src/lib/.venv/bin:$PATH"
RUN python -m venv .venv && /usr/src/lib/.venv/bin/pip install --upgrade pip

COPY redbrick-sdk/*.whl ./
RUN pip install *.whl && rm *.whl

WORKDIR /usr/src/app
CMD ["python"]  # ["redbrick"]

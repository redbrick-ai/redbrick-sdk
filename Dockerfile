FROM python:3.12-slim
WORKDIR /usr/src/lib

ENV VIRTUAL_ENV="/usr/src/lib/.venv" PATH="/usr/src/lib/.venv/bin:$PATH"
RUN python -m venv .venv && /usr/src/lib/.venv/bin/pip install --upgrade pip

COPY redbrick-sdk/redbrick-sdk-*.tar.gz redbrick-sdk.tar.gz
RUN pip install redbrick-sdk.tar.gz && rm redbrick-sdk.tar.gz

WORKDIR /usr/src/app
CMD ["python"]  # ["redbrick"]

FROM python:3.12-slim

WORKDIR /usr/src/app

RUN python -m venv .venv
RUN pip install --upgrade pip redbrick-sdk

ENV VIRTUAL_ENV=/usr/src/app/.venv
ENV PATH="/usr/src/app/.venv/bin:$PATH"

CMD ["python"]

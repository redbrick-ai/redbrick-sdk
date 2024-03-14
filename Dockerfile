FROM python:3.12-slim
WORKDIR /usr/src/app
ENV VIRTUAL_ENV="/usr/src/app/.venv" PATH="/usr/src/app/.venv/bin:$PATH"
RUN python -m venv .venv && pip install --upgrade pip redbrick-sdk
CMD ["python"]

FROM python:3.11.2-slim-bullseye
LABEL maintainer="klusowskimat@gmail.com"

ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app

WORKDIR /app
EXPOSE 8000

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apt-get update && \
    apt-get install -y \
        gcc \
        python3-dev \
        libpq-dev \
        postgresql-client \
        libjpeg-dev \
        libheif-dev \
        libde265-dev \
        libffi-dev \
        musl-dev &&\
    /py/bin/pip install --no-compile -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        app-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R app-user:app-user /vol && \
    chmod -R 755 /vol

ENV PATH="/py/bin:$PATH"

USER app-user

FROM python:3.11-slim-bookworm

ARG DBT_VERSION=1.9.1
ARG GE_VERSION=0.18.15

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DBT_PROFILES_DIR=/usr/local/dbt

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
        git \
        curl \
        make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY docker/tools/requirements.txt /tmp/requirements-tools.txt
RUN pip install --no-cache-dir -r /tmp/requirements-tools.txt

WORKDIR /usr/local/dbt
CMD ["bash"]

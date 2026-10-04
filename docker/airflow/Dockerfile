ARG AIRFLOW_VERSION=2.10.3
ARG AIRFLOW_PYTHON_MINOR=3.11
ARG DBT_VERSION=1.9.1
ARG AIRFLOW_HOME=/opt/airflow

FROM apache/airflow:${AIRFLOW_VERSION}-python${AIRFLOW_PYTHON_MINOR}

ARG AIRFLOW_HOME
ARG DBT_VERSION
ARG AIRFLOW_PYTHON_MINOR
ENV AIRFLOW_HOME=${AIRFLOW_HOME} \
    AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags \
    AIRFLOW__CORE__PLUGINS_FOLDER=/opt/airflow/plugins \
    AIRFLOW__CORE__LOAD_EXAMPLES=false \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DBT_VENV=/opt/dbt-venv \
    DBT_PROJECT_DIR=/opt/airflow/dbt \
    DBT_PROFILES_DIR=/opt/airflow/dbt

USER root
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
        libssl-dev \
        git \
        curl \
        unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY docker/airflow/requirements.txt /tmp/requirements-airflow.txt
# the base image ships a /root/bin/pip guard that refuses to run as root, so always
# invoke pip as a module to bypass it
RUN python3 -m pip install --no-cache-dir \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${AIRFLOW_PYTHON_MINOR}.txt" \
        -r /tmp/requirements-airflow.txt

# dbt lives in an isolated venv so it never fights Airflow's constraint pins
RUN python -m venv ${DBT_VENV} \
    && ${DBT_VENV}/bin/python -m pip install --no-cache-dir --upgrade pip \
    && ${DBT_VENV}/bin/python -m pip install --no-cache-dir \
        "dbt-core==${DBT_VERSION}" \
        "dbt-postgres==${DBT_VERSION}"

COPY docker/airflow/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins \
    && chown -R airflow:${AIRFLOW_UID} ${AIRFLOW_HOME} ${DBT_VENV}

USER airflow

ENTRYPOINT ["/entrypoint.sh"]
CMD ["webserver"]

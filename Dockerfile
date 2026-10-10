FROM apache/airflow:3.3.0-python3.11

COPY --chown=airflow:root pyproject.toml /opt/airflow/project/
COPY --chown=airflow:root src/ /opt/airflow/project/src/

RUN pip install --no-cache-dir /opt/airflow/project
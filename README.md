# YouTube Opportunity Finder

Turkish-first, multilingual-capable data platform for discovering YouTube content opportunities.

## What this first lesson contains

- **Postgres** stores Airflow metadata today and our product data later.
- **Airflow webserver** gives us the UI at <http://localhost:8080>.
- **Airflow scheduler** decides when pipeline tasks should run.
- **A DAG** demonstrates the smallest possible `extract -> transform -> load` pipeline.
- **Docker Compose** starts these cooperating containers as one local stack.

## Lesson 1: run the stack

Docker Desktop must be running. Then:

```bash
cp .env.example .env
docker compose up airflow-init
docker compose up -d
docker compose ps
```

Open <http://localhost:8080> and sign in with `admin` / `admin`. Find
`hello_youtube_pipeline`, switch it on, and trigger it manually.

To inspect logs:

```bash
docker compose logs -f airflow-scheduler
```

To stop containers without deleting the database volume:

```bash
docker compose down
```

## Mental model

An **image** is a reusable recipe. A **container** is a running instance of that
recipe. A **volume** keeps data when a container stops. A **service** is one
container role in Compose. A **DAG** is Airflow's graph of pipeline tasks.

## Planned architecture

```text
source payloads -> raw -> staging/process -> semantic/data product -> dashboard
```

V1 will expose Turkish data in the semantic layer while preserving language and
locale fields upstream so English and German can be added later.

## Next lesson

Replace the hard-coded example with Turkish YouTube autocomplete ingestion, save
immutable raw responses, and load normalized questions idempotently into Postgres.


from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="hello_youtube_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["learning", "youtube"],
)
def hello_youtube_pipeline():
    """Our first tiny pipeline: extract -> transform -> load."""

    @task
    def extract() -> list[str]:
        return ["nasıl youtube kanalı açılır", "youtube seo nedir"]

    @task
    def transform(questions: list[str]) -> list[str]:
        return [question.strip().lower() for question in questions]

    @task
    def load(questions: list[str]) -> None:
        for question in questions:
            print(f"Ready for the semantic layer: {question}")

    load(transform(extract()))


hello_youtube_pipeline()


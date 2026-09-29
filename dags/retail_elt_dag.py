"""
Retail ELT pipeline DAG.

Flow: raw load (one task per source table, run sequentially since they all
write to the same single-file DuckDB warehouse) -> dbt build (staging +
marts + all tests, in one dependency-ordered run). dbt build stops on the
first failing test, so a bad row anywhere in the DAG fails this task --
and therefore the whole DAG run -- rather than continuing silently into a
green pipeline with wrong numbers underneath it.

Each load task is idempotent: re-running it for a month that already
landed replaces that month's rows rather than appending, so re-triggering
this DAG never duplicates data.
"""
from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

DATA_DIR = "/opt/airflow/data"
WAREHOUSE_PATH = f"{DATA_DIR}/warehouse/retail.duckdb"
LANDING_DIR = f"{DATA_DIR}/landing"
SEED_DIR = f"{DATA_DIR}/seed"
DBT_PROJECT_DIR = "/opt/airflow/dbt/retail_elt"
DBT_PROFILES_DIR = "/opt/airflow/dbt/profiles"


def load_table(table_name, **_):
    import subprocess
    import sys

    cmd = [
        sys.executable,
        "/opt/airflow/scripts/load_raw.py",
        "--warehouse", WAREHOUSE_PATH,
        "--landing", LANDING_DIR,
        "--seed", SEED_DIR,
        "--table", table_name,
    ]
    subprocess.run(cmd, check=True)


default_args = {
    "owner": "retail_elt",
    "retries": 0,
}

with DAG(
    dag_id="retail_elt_pipeline",
    description="Landing zone -> raw load -> dbt build (transform + test)",
    default_args=default_args,
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["elt", "dbt", "duckdb"],
) as dag:

    load_tasks = []
    for table in ["orders", "order_items", "payments", "reviews", "seed"]:
        task = PythonOperator(
            task_id=f"load_{table}",
            python_callable=load_table,
            op_kwargs={"table_name": table},
        )
        load_tasks.append(task)

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DUCKDB_PATH={WAREHOUSE_PATH} "
            f"dbt build --profiles-dir {DBT_PROFILES_DIR} --project-dir {DBT_PROJECT_DIR}"
        ),
    )

    chain(*load_tasks, dbt_build)

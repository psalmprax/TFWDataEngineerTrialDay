from datetime import datetime
from airflow.hooks.postgres_hook import PostgresHook
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.mysql_hook import MySqlHook
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
# from airflow.contrib.hook.slack_webhook_operator import SlackWebhookOperator
# from airflow.contrib.hooks.slack_webhook_hook import SlackWebhookHook
from config import Config
# import psycopg2
from airflow.models.baseoperator import BaseOperator
from sqlalchemy import create_engine

cfg = Config()

dag_params = {
    'dag_id': 'Ingest',
    'start_date': datetime(2020, 3, 29),
    'schedule_interval': None
}


def copy(ds, **kwargs):
    source_query = """select * from address;"""
    dest_query = "insert into address values %s"

    source_hook = create_engine('postgresql+psycopg2://airflow:airflow@postgres/airflow')
    source_conn = source_hook.connect()
    records = source_conn.execute(source_query)
        
    dest_hook = MySqlHook(mysql_conn_id="target", schema="mysql")
    dest_conn = dest_hook.get_conn()
    dest_cursor = dest_conn.cursor()
    
    if records:
        # logging.info("Inserting rows into MySQL")
        dest_hook.insert_rows(table="address", rows=records)
        
    dest_cursor.close()
    
    source_conn.close()
    dest_conn.close()
    

with DAG(**dag_params, template_searchpath=[cfg.dir_dag_template]) as dag:

    create_extension_task = PostgresOperator(
        task_id='create_extension',
        sql="create_extension.sql",
        postgres_conn_id="source"
    )


    create_source_table_and_insert_source_table = PostgresOperator(
        task_id='create_table',
        sql="set_up_python.sql",
        postgres_conn_id="source"
    )

    create_target_table_mysql = MySqlOperator(
        task_id='create_table_mysql',
        mysql_conn_id='target',
        sql='create_table_mysql.sql',
    )


    insert_source_table_no_duplicate = PostgresOperator(
          task_id='insert_target_table_no_duplicate',
          sql="insert_target_table_no_duplicate.sql",
          postgres_conn_id="source"
    )

    insert_target_table = PythonOperator(
          task_id='insert_target_table',
          python_callable=copy,
          provide_context=True
    )

    create_extension_task  >> create_source_table_and_insert_source_table >> insert_source_table_no_duplicate >> create_target_table_mysql >> insert_target_table





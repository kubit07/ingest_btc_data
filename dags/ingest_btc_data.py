from airflow import DAG
from datetime import datetime, timedelta
from airflow.sensors.http_sensor import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.postgres_operator import PostgresOperator


default_args = {
    "owner": "airflow",
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "nononsaa.david@gmail.com",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

def chek_github_data(response):
    if "Date" in response:
        return True
    else:
        return False

def save_bitcoins_data(response):
    with open('/opt/airflow/dags/btc_eur_data.csv', mode='w') as file:
        file.write(response)
    return True

    
with DAG('ingest_btc_data', description='Bitcoins Data Ingestion', schedule='@daily',
         start_date=datetime(2024, 4, 14), default_args=default_args, catchup=False) as dag:
    
    is_ingest_btc_data_available = HttpSensor(
        task_id="is_github_active",
        method="GET",
        http_conn_id="githubcon",
        endpoint="kubit07/ingest_btc_data/kubit/btc_eur_data.csv",
        response_check=lambda response: chek_github_data(response.text),
        poke_interval=5,
        timeout=20
    )

    get_bitcoins_data = SimpleHttpOperator(
        task_id="get_bitcoins_data",
        http_conn_id="githubcon",
        endpoint="kubit07/ingest_btc_data/kubit/btc_eur_data.csv",
        method="GET",
        response_filter=lambda response: save_bitcoins_data(response.text),
        log_response = True
    )

    create_table_msql = MySqlOperator(
        task_id="create_table_btc_eur_mysql",
        mysql_conn_id="mysqlcon",
        sql=r"""
            CREATE TABLE IF NOT EXISTS t_btc_eur(
            id_btc_eur INT AUTO_INCREMENT,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            adj_close DOUBLE,
            volume MEDIUMINT,
            PRIMARY KEY (id_btc_eur)
        );
        """
    )

    create_table_postgres = PostgresOperator(
        task_id='create_table_btc_eur_postgres',
        postgres_conn_id='postgrecon',
        sql=r"""
            CREATE TABLE IF NOT EXISTS t_btc_eur(
            id_btc_eur SERIAL PRIMARY KEY,
            date DATE,
            open DECIMAL,
            high DECIMAL,
            low DECIMAL,
            close DECIMAL,
            adj_close DECIMAL,
            volume SMALLINT
        );
        """
    )

    




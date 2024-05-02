from airflow import DAG
from datetime import datetime, timedelta
from airflow.sensors.http_sensor import HttpSensor
from airflow.operators.python_operator import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.hooks.mysql_hook import MySqlHook 
from airflow.hooks.postgres_hook import PostgresHook 
from yahoo_fin.stock_info import get_data


import pandas as pd

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


def get_bitcoins_data_yahoo(ti):
    bitcoin_eur_day = get_data("BTC-EUR", start_date="04/15/2023", end_date="05/01/2024", index_as_date = True, interval="1d")
    bitcoin_eur_day.to_csv('opt/airflow/dags/btc_eur_data_yahoo_api.csv', index=False)  



""" def insert_post_mysql_hook():
    mysql_hook = MySqlHook(mysql_conn_id='mysqlcon', schema='db')
    with open('/opt/airflow/dags/post.json') as f:
        data=f.read()
        djson=json.loads(data)
        postlist=[]
        for items in djson:
            postlist.append((items['id'],items['title']))
        target_fields = ['post_id', 'title']
        mysql_hook.insert_rows(table='Post', rows=postlist, target_fields=target_fields) """


def insert_post_mysql_hook():
    target_fields = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
    postlist=[]
    mysql_hook = MySqlHook(mysql_conn_id='mysqlcon', schema='db')
    # Read the CSV file
    df_ingest_btc_data = pd.read_csv("/opt/airflow/dags/btc_eur_data.csv")
    for index, row in df_ingest_btc_data.iterrows():
        postlist.append((row['Date'],row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume']))
    mysql_hook.insert_rows(table='t_btc_eur', rows=postlist, target_fields=target_fields)    


def insert_post_postgres_hook():
    target_fields = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
    postlist=[]
    mysql_hook = PostgresHook(postgres_conn_id='postgrecon', schema='db')
    # Read the CSV file
    df_ingest_btc_data = pd.read_csv("/opt/airflow/dags/btc_eur_data.csv")
    for index, row in df_ingest_btc_data.iterrows():
        postlist.append((row['Date'],row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume']))
    mysql_hook.insert_rows(table='t_btc_eur', rows=postlist, target_fields=target_fields) 

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

    get_bitcoins_data_github = SimpleHttpOperator(
        task_id="get_bitcoins_data_github",
        http_conn_id="githubcon",
        endpoint="kubit07/ingest_btc_data/kubit/btc_eur_data.csv",
        method="GET",
        response_filter=lambda response: save_bitcoins_data(response.text),
        log_response = True
    )

    get_bitcoins_data_yahoo_fin = PythonOperator(
        task_id="get_bitcoins_data_yahoo_fin",
        python_callable=get_bitcoins_data_yahoo
    )

    save_bitcoin_data_from_yahoo_api = PythonOperator(
        task_id="save_bitcoin_data_from_yahoo_api",
        python_callable=save_btc_data_api_yahoo
    )

    create_table_msql = MySqlOperator(
        task_id="create_table_btc_eur_mysql",
        mysql_conn_id="mysqlcon",
        sql=r"""

            DROP TABLE IF EXISTS t_btc_eur;

            CREATE TABLE IF NOT EXISTS t_btc_eur(
            id_btc_eur INT AUTO_INCREMENT,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            adj_close DOUBLE,
            volume BIGINT,
            PRIMARY KEY (id_btc_eur)
        );
        """
    )

    create_table_postgres = PostgresOperator(
        task_id='create_table_btc_eur_postgres',
        postgres_conn_id='postgrecon',
        sql=r"""

            DROP TABLE IF EXISTS t_btc_eur;

            CREATE TABLE IF NOT EXISTS t_btc_eur(
            id_btc_eur SERIAL PRIMARY KEY,
            date DATE,
            open DECIMAL,
            high DECIMAL,
            low DECIMAL,
            close DECIMAL,
            adj_close DECIMAL,
            volume BIGINT
        );
        """
    )

    insert_post_mysql_task = PythonOperator(
        task_id='insert_post_mysql_task',
        python_callable=insert_post_mysql_hook
    )

    insert_post_postgres_task = PythonOperator(
        task_id='insert_post_postgres_task',
        python_callable=insert_post_postgres_hook
    )





from airflow import DAG
from datetime import datetime 
from airflow.operators.bash_operator import BashOperator

with DAG('bash_dag_example', description='My Bash Dag', schedule='@daily',
         start_date=datetime(2024, 4, 14), catchup=False) as dag:
    
    mytask = BashOperator(task_id='first_bash_task',bash_command="whoami;echo Dave Saa")

    mytask




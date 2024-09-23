import io
import os
import psycopg2
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from configparser import ConfigParser
from os.path import join, dirname, abspath

base_path = dirname(abspath(__file__))

config = ConfigParser(interpolation=None)
config.read(join(base_path, 'config.ini'))

def update_api_status(api_id, status):
    table = config['table']['service']
    query = f"UPDATE {table} SET status = '{status}' WHERE id_api = {api_id};"
    
    try:
        connection = psycopg2.connect(
            user=config['auth']['user'],
            password=config['auth']['password'],
            host=config['auth']['host'],
            database=config['auth']['database']
        )
        
        connection.autocommit = True 
        
        with connection.cursor() as cursor:
            cursor.execute(query)
        
        connection.commit()
        
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    
    finally:
        if connection:
            connection.close()

def connect_db():
     # Create Engine Database
    username = config['auth']['user']
    password = config['auth']['password']
    host = config['auth']['host']
    database_name = config['auth']['database']
    
    machine = create_engine(config['connection']['engine'] % (username, password, host, database_name))
    conn = machine.raw_connection()
    conn.set_client_encoding(config['connection']['encoding'])
    conn.set_client_encoding(config['connection']['encodings'])
    cursor = conn.cursor()
    cursor.execute("SET SCHEMA 'mb'")
    
    return conn, cursor

def append_data(**kwargs):
    columns = []
    data = [[]]
    for key , value in kwargs.items() :
        columns.append(key),
        data[0].append(value)
        
    df =  pd.DataFrame(data, columns = columns)
    df.request_date = pd.to_datetime(df.request_date , format = 'Y%-m%-d%  H%:M%:S%')

    conn, cursor = connect_db()

    conn.autocommit = True
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    contents = output.getvalue()
    cursor.copy_from(output, '{}'.format(config['table']['analytics']), columns=df.columns, null="") # null values become ''
    conn.commit()

    cursor.close()
    conn.close()

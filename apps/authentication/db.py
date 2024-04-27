from multiprocessing import connection
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
#import pyodbc
import pymysql

engine = create_engine('mysql+pymysql://root:@localhost:3307/visualitiApisDB',
    isolation_level="READ UNCOMMITTED", future=True)

conn = engine.connect()
meta = MetaData()

def execute_query(query):
    engineForConn = engine

    while True:
        try:
            # Intenta ejecutar la consulta
            with engineForConn.connect() as connx:
                result = connx.execute(text(query))
                # Realiza cualquier otra operación necesaria aquí
                return result.fetchall()
        except OperationalError as e:
            if "Lost connection to MySQL server during query" in str(e):
                # Reconexión si se perdió la conexión durante la consulta
                continue
            else:
                raise e

def insert_update_query(query):
    engineForConn = engine

    while True:
        try:
            # Intenta ejecutar la consulta
            with engineForConn.connect() as connx:
                connx.execute(text(query))
                # Realiza cualquier otra operación necesaria aquí
                return connx.commit()
        except OperationalError as e:
            if "Lost connection to MySQL server during query" in str(e):
                # Reconexión si se perdió la conexión durante la consulta
                continue
            else:
                raise e

def next_sequence(sequence):
    engineForConn = engine
    
    call = ('CALL getNextSequenceValue(\'' + sequence + '\', @next_value)')
    query = ('SELECT @next_value AS next_value;')


    while True:
        try:
            # Intenta ejecutar la consulta
            with engineForConn.connect() as connx:
                connx.execute(text(call))
                connx.commit()
                result = connx.execute(text(query))
                # Realiza cualquier otra operación necesaria aquí
                return result.fetchall()
        except OperationalError as e:
            if "Lost connection to MySQL server during query" in str(e):
                # Reconexión si se perdió la conexión durante la consulta
                continue
            else:
                raise e
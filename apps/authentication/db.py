from multiprocessing import connection
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
import pyodbc
import pymysql

# engine = create_engine("mssql+pyodbc://db_a96059_geobalancehidrico_admin:Asdfqwer1234@SQL8004.site4now.net:1433/db_a96059_geobalancehidrico?driver=ODBC+Driver+17+for+SQL+Server")
engine = create_engine('mysql+pymysql://dbagreeniti:5Qdw5D3b79PbUDuJ@localhost:3306/visualitiApisDB',
    isolation_level="READ UNCOMMITTED", future=True)

conn = engine.connect()

engine2 = create_engine('mysql+pymysql://dbagreeniti:5Qdw5D3b79PbUDuJ@localhost:3306/greenitidb',
    isolation_level="READ UNCOMMITTED")

conn2 = engine2.connect()
meta = MetaData()

def execute_query(tipo, query):
    engineForConn = engine
    if (tipo == 2):
        engineForConn = engine2

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

def insert_update_query(tipo, query):
    engineForConn = engine
    if (tipo == 2):
        engineForConn = engine2

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
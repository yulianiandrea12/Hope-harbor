from multiprocessing import connection
from sqlalchemy import create_engine, MetaData
import pyodbc

engine = create_engine("mssql+pyodbc://SA:root1234.@localhost:1433/GeoBalanceHidrico?driver=ODBC+Driver+17+for+SQL+Server")

conn= engine.connect()
meta=MetaData()

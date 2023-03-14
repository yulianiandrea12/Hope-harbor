from multiprocessing import connection
from sqlalchemy import create_engine, MetaData
import pyodbc

engine = create_engine("mssql+pyodbc://db_a96059_geobalancehidrico_admin:Asdfqwer1234@SQL8004.site4now.net:1433/db_a96059_geobalancehidrico?driver=ODBC+Driver+17+for+SQL+Server")

conn= engine.connect()
meta=MetaData()

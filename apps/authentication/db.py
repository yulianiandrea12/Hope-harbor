from multiprocessing import connection
from sqlalchemy import create_engine, MetaData
import pyodbc
import pymysql

# engine = create_engine("mssql+pyodbc://db_a96059_geobalancehidrico_admin:Asdfqwer1234@SQL8004.site4now.net:1433/db_a96059_geobalancehidrico?driver=ODBC+Driver+17+for+SQL+Server")
# engine = create_engine('mysql+pymysql://dbagreeniti:5Qdw5D3b79PbUDuJ@localhost:3306/visualitiApisDB')
engine = create_engine('mysql://root:root@localhost:3306/visualitiApisDB')

conn= engine.connect()
meta=MetaData()

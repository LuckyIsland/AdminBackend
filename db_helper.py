import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
import urllib

from configs import DBConfig


quoted = urllib.quote_plus(
    'DRIVER={FreeTDS};Server=%(SERVER)s;Database=%(DATABASE)s;UID=%(USERNAME)s;PWD=%(PASSWORD)s;TDS_Version=8.0;Port=%(PORT)s;' % DBConfig
    )
engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(quoted))
Session = sessionmaker(bind=engine)

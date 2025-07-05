import mysql.connector

host = 'localhost'
user = 'root'
password = ''
database = 'makeathondb'

conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password
)

cursor = conn.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
conn.commit()
cursor.close()
conn.close()

conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

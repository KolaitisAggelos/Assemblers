import mysql.connector

# Connection parameters
host = 'localhost'
database = 'makeathondb'

# Connect to the database
conn = mysql.connector.connect(
    host=host,
    database=database,
    user="root"
)



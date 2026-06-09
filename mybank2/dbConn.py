import mysql.connector

def getConnection():
     return mysql.connector.connect(
          host="127.0.0.1",
          user="root",
          password="761399",
          database="mybank"
     )
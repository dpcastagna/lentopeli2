import mysql.connector

def yhteys():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        database='flight_game',
        user='root',
        password='kissakoira',
        autocommit=True,
        use_pure=True
    )
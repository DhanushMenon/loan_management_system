import psycopg2

try:
    connection = psycopg2.connect(
        database="loan_management",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )
    print("Database connected successfully!")
except Exception as e:
    print(f"Error connecting to database: {e}")
finally:
    if 'connection' in locals():
        connection.close() 
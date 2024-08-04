from flask import Flask
from prometheus_client import Counter, Histogram, generate_latest
import psycopg2
import time

app = Flask(__name__)

# Prometheus metrics
http_request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP Request Duration in seconds', ['method', 'endpoint'])

# Database connection settings
db_params = {
    'dbname': 'your_db_name',
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'db-service',
    'port': '5432'
}

@app.route('/')
@http_request_duration.labels(method='GET', endpoint='/').time()
def index():
    http_request_counter.labels(method='GET', endpoint='/').inc()
    
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        current_time = cursor.fetchone()[0]
        return f"Hello World! Current time is: {current_time}"
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        connection.close()

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)


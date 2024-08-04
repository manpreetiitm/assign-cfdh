from flask import Flask, request
from prometheus_client import Counter, Histogram, generate_latest
import psycopg2
import time

app = Flask(__name__)

# Prometheus metrics
http_request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP Request Duration in seconds', ['method', 'endpoint'])
http_response_status_counter = Counter('http_response_status_total', 'Total HTTP Response Status Codes', ['method', 'endpoint', 'status_code'])

# Database connection settings
db_params = {
    'dbname': 'newdb',
    'user': 'admin',
    'password': 'admin',
    'host': 'db-service',
    'port': '5432'
}

@app.route('/')
def index():
    method = request.method
    endpoint = '/'
    
    http_request_counter.labels(method=method, endpoint=endpoint).inc()
    
    start_time = time.time()
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        current_time = cursor.fetchone()[0]
        response = f"Hello World! Current time is: {current_time}"
        status_code = 200
    except Exception as e:
        response = f"Database error: {str(e)}"
        status_code = 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
    # Measure duration
    duration = time.time() - start_time
    http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    # Count the status code
    http_response_status_counter.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    
    return response, status_code

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)


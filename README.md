# assign-cfdh
## Step 1: Build a Docker Image for a Custom Application with PostgreSQL

### Python Flask Application (`app.py`)

Create a file named `app.py` with the code that connects to PostgreSQL:

```
from flask import Flask, jsonify, request
import psycopg2
from prometheus_client import start_http_server, Counter
import time

app = Flask(__name__)

# PostgreSQL Setup
connection = psycopg2.connect(
    dbname="metricsDB",
    user="postgres",
    password="password",
    host="postgres.custom-app.svc.cluster.local",  # Adjust for Kubernetes service
    port="5432"
)
cursor = connection.cursor()

# Metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total number of requests', ['method', 'path'])

@app.route('/items', methods=['POST'])
def create_item():
    item_name = request.json.get('name', 'default_item')
    
    # Insert into PostgreSQL
    cursor.execute("INSERT INTO items (name) VALUES (%s);", (item_name,))
    connection.commit()

    # Log metrics
    REQUEST_COUNT.labels(method='POST', path='/items').inc()
    return jsonify({"name": item_name}), 201

@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify({
        'total_requests': REQUEST_COUNT.collect()[0].samples[0].value
    })

if __name__ == "__main__":
    start_http_server(8001)  # Exposing /metrics on port 8001
    app.run(host='0.0.0.0', port=5000)
```

## Step 2: Create Dockerfile ##

##dockerfile##

```
# Use the official Python image
FROM python:3.9

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py ./

# Expose the application port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]
```

## Step 2: Create requirements.txt ##

```
Flask==2.2.2
psycopg2-binary==2.9.5
prometheus_client==0.15.0
```

## Step 3: Build the Docker Image ##

```
docker build -t my-python-app .
```

## Step 4. Create the namespaces YAMLs ##

```
apiVersion: v1
kind: Namespace
metadata:
  name: custom-app
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
```
### Step 5: Create namespaces using YAMLs ##

```
kubectl apply -f namespaces.yaml

```




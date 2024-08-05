# assign-cfdh
## Step 1: Build a Docker Image for a Custom Application with PostgreSQL

### Python Flask Application (`app.py`)

Create a file named `app.py` with the code that connects to PostgreSQL:

```
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
psycopg2-binary==2.9
prometheus_client==0.14.1
Werkzeug==2.2.2

```

## Step 3: Build the Docker Image ##

```
docker build -t my-python-app .


```

## Step 4: Tag the docker image and push to dockerhub ##

```
docker tag custom-python-app:v1 manpreetiitm/custom-python-app:v1

docker push manpreetiitm/custom-python-app:v1
```

## Step 4. Create the namespaces YAMLs ##

```
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: custom-python-app-namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring-namespace
```
### Step 5: Create namespaces using YAMLs ##

```
kubectl apply -f namespaces.yaml

```

### Step 6: Create app deployment and service YAML ##

```

apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-python-app
  namespace: custom-python-app-namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: custom-python-app
  template:
    metadata:
      labels:
        app: custom-python-app
    spec:
      containers:
      - name: custom-python-app
        image: manpreetiitm/custom-python-app:v3
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          value: "postgresql://admin:admin@postgres.db-service.custom-python-app-namespace.svc.cluster.local:5432/newdb"
---
apiVersion: v1
kind: Service
metadata:
  name: custom-python-app
  namespace: custom-python-app-namespace 
spec:
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: my-python-app

```


### Step 7: Create db deployment and service YAML ##

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: db
  namespace: custom-python-app-namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
          - name: POSTGRES_USER
            value: admin 
          - name: POSTGRES_PASSWORD
            value: admin 
          - name: POSTGRES_DB
            value: newdb 
        ports:
          - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: db-service
  namespace: custom-python-app-namespace
spec:
  ports:
    - port: 5432
  selector:
    app: db

```

### Step 7: Create PostgreSQL Tables ##

1. Connect to PostgreSQL:
   
   Once the PostgreSQL pod is up, you can run the following command to execute psql:

```
   kubectl exec -it <postgres_pod_name> -n custom-python-app-namespace -- psql -U postgres -d newdb
```

2. Create the Table:

```
  CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);
```
### Step 8: Set Up Prometheus and Grafana with Helm ##

1. Add Helm Chart Repositories:
   
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

2. Install Prometheus:

```
helm install prometheus prometheus-community/prometheus --namespace monitoring-namespace
```

3. Instal Grafana:

```
helm install grafana grafana/grafana --namespace monitoring-namespace
```

4. Create a new ConfigMap YAML file called prometheus-config.yaml:

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring-namespace
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
      - job_name: 'custom-python-app'
        metrics_path: '/metrics'
        static_configs:
          - targets: ['custom-python-app.custom-python-app-namespace.svc.cluster.local:3000']
```

5. Apply the ConfigMap:

```
kubectl apply -f prometheus-config.yaml
```

6. Restarting Prometheus to Apply Changes

```
kubectl rollout restart deployment <prometheus-deployment-name> -n monitoring-namespace
```

7. Deploy Node Exporter Using Helm:

```
helm install node-exporter prometheus-community/prometheus-node-exporter \
  --namespace monitoring-namespace \
  --set prometheus.enabled=true \
  --set serviceMonitor.enabled=true
```

8. Update Prometheus to Scrape Node Exporter

   ```
   kubectl get configmaps -n monitoring-namespace
   ```
9. Edit the Prometheus Configuration:

```
groups:
  - name: kubernetes-nodes
    rules:
      - record: node_memory_utilization: gauge
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes
      - record: node_cpu_utilization: gauge
        expr: rate(node_cpu_seconds_total[5m])
```

10. Apply the Configuration Changes.

11. Setup Grafana Dashboard:

    Access Grafana:

```
kubectl port-forward service/grafana 3000:80 -n monitoring-namespace
```
   Access it at http://localhost:3000 with the default login admin/admin.

12.  Add Prometheus as a Data Source:
    a. Go to Configuration -> Data Sources in Grafana.
    b. Click on Add data source.
    c. Choose Prometheus and configure it with the URL http://prometheus-server.monitoring-namespace.svc.cluster.local:80.
    d. Click Save & Test.

13. Import Kubernetes Dashboards:

    Grafana has many pre-built dashboards for Kubernetes monitoring:

    a. Go to Create -> Import.
    b. Input the dashboard ID for Kubernetes Dashboard, such as 6417 or 3119, and click Import. These IDs are for community dashboards that you can find in the Grafana dashboard repository.
    c. Choose your Prometheus data source.

14. Visualize Node Metrics:
    The imported dashboard will provide an overview of node metrics, including CPU usage, memory usage, network I/O, disk I/O, etc.

## Step 9: Monitoring Pods ##

Import pre-built Grafana dashboards to visualize pod metrics.
   








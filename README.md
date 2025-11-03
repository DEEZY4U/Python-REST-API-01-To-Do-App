# Flask To-Do List REST API

A production-ready Flask REST API for managing to-do items, designed for AWS deployment with Terraform.

## Features

- ✅ Full CRUD operations for to-do items
- ✅ MySQL database backend
- ✅ Health check endpoint for load balancers
- ✅ Environment-based configuration
- ✅ CORS enabled
- ✅ RESTful API design
- ✅ Production-ready error handling

## API Endpoints

### Health Check
- `GET /health` - Health check for load balancers

### Root
- `GET /` - API information and available endpoints

### To-Do Operations
- `GET /api/todos` - Get all todos (supports `?status=pending|in-progress|completed`)
- `GET /api/todos/<id>` - Get a specific todo
- `POST /api/todos` - Create a new todo
- `PUT /api/todos/<id>` - Update a todo
- `DELETE /api/todos/<id>` - Delete a todo

## To-Do Item Structure

```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Finish the Flask API project",
  "status": "in-progress",
  "created_at": "2025-11-03T10:00:00",
  "updated_at": "2025-11-03T10:30:00"
}
```

**Status values:** `pending`, `in-progress`, `completed`

## Local Setup

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or 8.0+

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd python-flask-todo-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a MySQL database:
```sql
CREATE DATABASE todo_db;
```

5. Set environment variables:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=todo_db
export PORT=5000
```

Or create a `.env` file:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=todo_db
PORT=5000
```

6. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## AWS Deployment

### Environment Variables for EC2/ECS

Set these environment variables in your AWS deployment:

```bash
DB_HOST=<your-rds-endpoint>
DB_USER=<your-db-username>
DB_PASSWORD=<your-db-password>
DB_NAME=todo_db
PORT=5000
```

### Using with Terraform

Example user data script for EC2:

```bash
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git

# Clone your repository
cd /home/ec2-user
git clone <your-repo-url>
cd python-flask-todo-api

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export DB_HOST=${db_endpoint}
export DB_USER=${db_user}
export DB_PASSWORD=${db_password}
export DB_NAME=todo_db

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### RDS Setup

Create a MySQL database in RDS and ensure:
- Security group allows inbound traffic on port 3306 from your EC2 instances
- Database is created: `CREATE DATABASE todo_db;`
- The application will automatically create the `todos` table on first run

### Load Balancer Configuration

Configure your ALB/ELB health check:
- Health check path: `/health`
- Expected response: `200 OK`
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 5 seconds
- Interval: 30 seconds

## API Usage Examples

### Create a To-Do

```bash
curl -X POST http://localhost:5000/api/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "status": "pending"
  }'
```

### Get All To-Dos

```bash
curl http://localhost:5000/api/todos
```

### Filter by Status

```bash
curl http://localhost:5000/api/todos?status=completed
```

### Get Specific To-Do

```bash
curl http://localhost:5000/api/todos/1
```

### Update a To-Do

```bash
curl -X PUT http://localhost:5000/api/todos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

### Delete a To-Do

```bash
curl -X DELETE http://localhost:5000/api/todos/1
```

## Production Deployment

For production, use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or create a systemd service file `/etc/systemd/system/todo-api.service`:

```ini
[Unit]
Description=Todo API Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/python-flask-todo-api
Environment="DB_HOST=<rds-endpoint>"
Environment="DB_USER=<username>"
Environment="DB_PASSWORD=<password>"
Environment="DB_NAME=todo_db"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable todo-api
sudo systemctl start todo-api
```

## Security Considerations

- Store credentials in AWS Secrets Manager or Parameter Store
- Use IAM roles for EC2 instances to access RDS
- Enable SSL/TLS for database connections
- Use HTTPS with ALB/CloudFront
- Implement rate limiting for production
- Add authentication/authorization as needed

## Monitoring

- Application logs are sent to stdout (compatible with CloudWatch Logs)
- Health check endpoint for monitoring
- Consider adding application metrics (Prometheus, CloudWatch)

## License

MIT License

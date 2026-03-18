FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy HTML files
COPY login.html login.html
COPY witt-classic.html witt-classic.html
COPY league-standings.html league-standings.html
COPY admin.html admin.html
COPY betting.html betting.html

# Expose port (Scaleway uses PORT env variable)
ENV PORT=8080
EXPOSE 8080

# Start the application (SQLAlchemy will auto-create tables)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

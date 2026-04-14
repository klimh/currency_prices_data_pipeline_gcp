FROM python:3.13-slim
WORKDIR /app

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY solver.py .

# Setup an app user so the container doesn't run as the root user
RUN useradd -m myuser
USER myuser

ENV PORT = 8080

CMD ["sh", "-c", "uvicorn solver:app --host 0.0.0.0 --port ${PORT}"]
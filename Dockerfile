<<<<<<< HEAD
FROM python:3.10-slim
=======
FROM python:3.11-slim
>>>>>>> f50d3e2 (Initial commit: Cloud Run Monitoring App)

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

<<<<<<< HEAD
CMD ["gunicorn", "-b", ":8080", "main:app"]
=======
ENV PORT 8080

CMD ["python", "main.py"]
>>>>>>> f50d3e2 (Initial commit: Cloud Run Monitoring App)

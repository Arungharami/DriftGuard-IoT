# Build from repository root: docker build -f apps/inference-space/Dockerfile .
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 app
WORKDIR /app
COPY pyproject.toml README.md ./
COPY requirements ./requirements
COPY src ./src
RUN pip install --no-cache-dir '.[platform]' -c requirements/constraints-py311.txt
COPY apps/inference-space/app.py ./app.py
USER app
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

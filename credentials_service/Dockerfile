FROM oven/bun AS frontend

WORKDIR /app
COPY frontend/package*.json ./
RUN bun i
COPY frontend/ .
RUN bun run build


FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend /app/dist /app/frontend

CMD ["python3", "app.py"]

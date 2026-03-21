FROM python:3.11-slim
WORKDIR /app
COPY Pipfile ./
# Allow pipenv to generate the lockfile during build if it is missing
RUN pip install pipenv && pipenv install --system --skip-lock
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
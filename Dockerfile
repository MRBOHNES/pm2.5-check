FROM python:3.14-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# the OpenAQ key is passed at run time (--env-file .env), never baked into the image
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

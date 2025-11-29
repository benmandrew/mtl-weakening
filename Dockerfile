
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential expect \
	&& rm -rf /var/lib/apt/lists/*

COPY . /app/

ENV NUXMV_PATH="/app/tools/nuXmv"

RUN pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./case-studies.sh"]

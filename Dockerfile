
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

ENV NUXMV_PATH="/opt/nuXmv/bin/nuXmv"

RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl xz-utils \
	&& mkdir -p /opt \
	&& curl -fsSL "https://nuxmv.fbk.eu/theme/download.php?file=nuXmv-2.1.0-linux64.tar.xz" -o /tmp/nuxmv.tar.xz \
	&& tar -xJf /tmp/nuxmv.tar.xz -C /opt \
	&& rm /tmp/nuxmv.tar.xz \
	&& mv /opt/nuXmv-2.1.0-linux64 /opt/nuXmv \
	&& test -x "$NUXMV_PATH" \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./case-studies.sh"]

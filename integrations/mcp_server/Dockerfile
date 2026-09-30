FROM python:3.12-slim

WORKDIR /app
COPY integrations/mcp_server/requirements.txt /tmp/mcp-requirements.txt
RUN pip install --no-cache-dir -r /tmp/mcp-requirements.txt \
    && groupadd --gid 10001 paperview \
    && useradd --uid 10001 --gid paperview --no-create-home paperview \
    && mkdir /data \
    && chown paperview:paperview /data
COPY integrations /app/integrations

USER paperview
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "-m", "integrations.mcp_server.server"]

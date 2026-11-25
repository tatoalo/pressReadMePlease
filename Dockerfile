FROM ubuntu:24.04

ENV TZ=Europe/Paris
ARG DEBIAN_FRONTEND=noninteractive

COPY --chmod=777 pressreader-cron /var/spool/cron/crontabs/root
COPY --chmod=777 entrypoint.sh /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    ca-certificates \
    libatomic1 \
    curl \
    cron \
    tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:$PATH"

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock /
RUN UV_PROJECT_ENVIRONMENT=/opt/venv uv sync --project / --locked --no-dev \
    --no-install-project --no-python-downloads --no-cache && \
    python -m playwright install chromium && \
    python -m playwright install-deps chromium && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY src/*.py src/

CMD ["/usr/local/bin/entrypoint.sh"]

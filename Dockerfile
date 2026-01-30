# This tool was written by @keyiflerolsun | for @KekikAkademi

# * Docker Image
FROM python:3.13.7-slim-trixie

# * Non-interactive apt/locale setup
ENV DEBIAN_FRONTEND=noninteractive

# * Use a safe locale during build (C.UTF-8 comes pre-installed)
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# * Workspace
WORKDIR /usr/src/ExampleProvider
COPY ./ /usr/src/ExampleProvider

# * Install locales and generate TR locale
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        # git \
        # ffmpeg \
        # opus-tools \
        locales \
        curl \
        tzdata && \
    sed -i 's/^# *tr_TR.UTF-8 UTF-8/tr_TR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen tr_TR.UTF-8 && \
    update-locale LANG=tr_TR.UTF-8 LC_ALL=tr_TR.UTF-8 LANGUAGE=tr_TR:tr && \
    ln -fs /usr/share/zoneinfo/Europe/Istanbul /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# * Standard environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING="UTF-8" \
    LANG="tr_TR.UTF-8" \
    LC_ALL="tr_TR.UTF-8" \
    LANGUAGE="tr_TR:tr" \
    TZ="Europe/Istanbul"

# * Install dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -U setuptools wheel && \
    python3 -m pip install --no-cache-dir -Ur requirements.txt

# * Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3310/api/v1/health || exit 1

# * Start the Application
CMD ["python3", "run.py"]
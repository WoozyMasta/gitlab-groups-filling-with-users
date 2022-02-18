# Define base images and tags
# ---------------------------
ARG DOCKERFILE_BUILD_IMAGE="docker.io/python"
ARG DOCKERFILE_BUILD_TAG="3.10-slim-bullseye"
ARG DOCKERFILE_BASE_IMAGE="docker.io/python"
ARG DOCKERFILE_BASE_TAG="3.10-alpine3.15"

# Build env
# ---------
FROM $DOCKERFILE_BUILD_IMAGE:$DOCKERFILE_BUILD_TAG as build

ARG PIP_INDEX_URL=https://pypi.org/simple/
ARG PIP_INDEX=https://pypi.org/pypi/
ENV PATH "/app/.venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt app.py ./
# Install latest whell and pip
# hadolint ignore=DL3013
RUN set -eux && \
    python -m venv .venv && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade wheel && \
    pip install --no-cache-dir --upgrade --requirement requirements.txt

# Create generator image
# ----------------------
FROM $DOCKERFILE_BASE_IMAGE:$DOCKERFILE_BASE_TAG

WORKDIR /app
COPY --from=build /app /app
ENV PATH "/app/.venv/bin:$PATH"

ENTRYPOINT ["/app/generator.py"]

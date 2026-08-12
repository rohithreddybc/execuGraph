# ExecuGraph reproducibility container.
#
# Builds a CUDA-enabled Python environment with all Python dependencies.
# Ollama itself is *not* shipped inside this container — it should run on
# the host (or a sibling container) so it can use the GPU directly.
#
# Run with: docker run --network=host execugraph python scripts/run_experiment.py ...
# (network=host so the container can reach the host's `ollama serve` on
# localhost:11434.)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[hf,dev]" || pip install -e ".[hf]"

COPY . .

# Default: print harness help so 'docker run execugraph' is informative.
CMD ["python", "scripts/run_experiment.py", "--help"]

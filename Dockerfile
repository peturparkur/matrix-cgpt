# syntax=docker/dockerfile:1
# Using ubuntu based image to be able to use poetry.
FROM python:3.11-slim-bullseye
ARG repo=https://github.com/peturparkur/matrix-cgpt.git

# Installing poetry, and other packages we will need (ssh, curl, git, bash, rsync, ...)
ENV PYTHONUNBUFFERED=1
RUN apt update -y && \
    apt install -y --no-install-recommends ssh curl git bash rsync psmisc && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 - && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
ENV PATH=$PATH:/etc/poetry/bin

# Clone application and install .venv
RUN git clone ${repo}
WORKDIR /matrix-cgpt
RUN poetry config virtualenvs.in-project true && poetry install

# Start application
CMD [ ".venv/bin/python3", "main.py" ] 
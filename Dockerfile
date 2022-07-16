FROM python:3.9


RUN true \
    && pip install poetry \
    && rm -rf /var/lib/apt/lists/* \
    && true

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
RUN poetry install

COPY crypto_monitor crypto_monitor
WORKDIR /

EXPOSE 8758

CMD ["poetry", "run", "python", "-um", "crypto_monitor.app"]
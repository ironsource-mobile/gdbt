FROM python:3.9-slim as builder

RUN pip install -q poetry

WORKDIR /usr/src/gdbt

COPY . /usr/src/gdbt/
RUN poetry build -f wheel


FROM python:3.9-slim as production

COPY --from=builder /usr/src/gdbt/dist/gdbt-*.whl /usr/src/gdbt/
RUN pip install -q /usr/src/gdbt/gdbt-*.whl && rm -f /usr/src/gdbt/gdbt-*.whl

CMD ["/bin/bash"]

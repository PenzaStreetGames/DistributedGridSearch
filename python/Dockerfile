FROM python:3.11 AS builder

WORKDIR /src/
LABEL author='Solomatin Pavel Nickolaevich'

USER root

COPY src .
ADD requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN chown -R daemon:daemon /src

FROM builder AS runner

WORKDIR /src/
EXPOSE 80

ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "80"]
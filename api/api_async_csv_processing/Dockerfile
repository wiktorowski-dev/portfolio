FROM public.ecr.aws/docker/library/python:3.11.5-bullseye

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /

COPY ./requirements.txt /backend/requirements.txt

RUN uv pip install --no-cache-dir --upgrade -r /backend/requirements.txt --system

COPY . .

ENTRYPOINT [ "python", "./main.py" ]

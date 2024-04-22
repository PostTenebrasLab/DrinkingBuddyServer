FROM docker.io/python:3.12
RUN --mount=type=bind,target=/context,rw \
    --mount=type=cache,target=/root/.cache \
    PYTHONDONTWRITEBYTECODE=1 \
    pip install /context --constraint /context/requirements.txt
EXPOSE 5000
ENTRYPOINT ["python", "-m", "DrinkingBuddyServer"]

FROM mcr.microsoft.com/devcontainers/python:3.14


# Node/npx are required because various MCP servers are primarily maintained
# and deployed via the node ecosystem.
RUN apt update && apt install -y \
    aview \
    imagemagick \
    nodejs \
    npm


RUN pip install --upgrade pip && \
    pip install uv

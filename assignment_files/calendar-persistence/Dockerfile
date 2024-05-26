# Use the official PostgreSQL image from the Docker Hub
FROM postgres:latest

# Add custom initialization script
COPY ./init.sql /docker-entrypoint-initdb.d/

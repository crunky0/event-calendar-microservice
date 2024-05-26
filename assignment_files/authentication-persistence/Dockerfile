# Use the official PostgreSQL image from the Docker Hub
FROM postgres:latest

# Add custom configuration or initialization scripts
COPY ./init.sql /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port
EXPOSE 5432

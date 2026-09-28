# Postgres 17 + pgvector con el script de inicialización dentro de la imagen
# (Coolify no garantiza los bind mounts de archivos del repo).
FROM pgvector/pgvector:pg17
COPY init-databases.sh /docker-entrypoint-initdb.d/10-init-databases.sh

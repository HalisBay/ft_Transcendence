#!/bin/bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Veritabanı varsa oluşturma
    DO \$(echo "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'") | grep -q 1 || \
        CREATE DATABASE $POSTGRES_DB;

    -- Kullanıcı varsa oluşturma
    DO \$(echo "SELECT 1 FROM pg_roles WHERE rolname = '$POSTGRES_USER'") | grep -q 1 || \
        CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';

    -- Kullanıcıya veritabanı üzerinde yetki ver
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL

exec docker-entrypoint.sh postgres

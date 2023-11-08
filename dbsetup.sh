#!/bin/bash

# File path to the .env file in your repository
ENV_FILE="./.env"

# Source the .env file to get the stored secrets
source $ENV_FILE

# Test the connection
PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -c "\q"
STATUS=$?
if [ $STATUS -ne 0 ]; then
    echo "Error: Could not connect to the server. Please check the hostname, username, and password."
    exit $STATUS
fi

# Check if the database 'cognimesh' exists
DB_EXISTS=$(PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -t -c "SELECT 1 FROM pg_database WHERE datname='cognimesh';")

if [ -z "$DB_EXISTS" ]; then
    # If 'cognimesh' doesn't exist, create it
    PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -c "CREATE DATABASE cognimesh WITH ENCODING 'UTF8' TEMPLATE template0;;"
    # Run tablesetup.sh to create tables
    ./database/tablesetup.sh
else
    # Check if the 'cognimesh' database is empty
    TABLE_COUNT=$(PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -d cognimesh -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    if [ "$TABLE_COUNT" -eq "0" ]; then
        # If empty, run tablesetup.sh to create tables
        ./database/tablesetup.sh
    else
        # If not empty, ask the user if they want to backup the database
        echo "The database 'cognimesh' is not empty. Do you want to backup the data first? (yes/no)"
        read BACKUP_ANSWER
        if [ "$BACKUP_ANSWER" == "yes" ]; then
            # Backup the data
            BACKUP_FILE="cognimesh_backup_$(date +%Y%m%d%H%M%S).sql"
            PGPASSWORD=$PG_PASS pg_dump -h $PG_HOST -U $PG_USER -d cognimesh > $BACKUP_FILE
            echo "Backup saved to $BACKUP_FILE. Download it to your computer and keep it safe."
        else
            # Clear the database
            PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -d cognimesh -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
            # Run tablesetup.sh to recreate the tables
            ./database/tablesetup.sh
        fi
    fi
fi

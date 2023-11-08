#!/bin/bash

# Set the file path to the .env file
ENV_FILE="./.env"

# Load the environment variables from the .env file
if [ -f "$ENV_FILE" ]; then
    source $ENV_FILE
else
    echo "Error: .env file not found."
    exit 1
fi

# Test the database connection
PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -c "\q"
STATUS=$?
if [ $STATUS -ne 0 ]; then
    echo "Error: Could not connect to the server. Please check the hostname, username, and password."
    exit $STATUS
fi

# Check if the 'cognimesh' database exists
DB_EXISTS=$(PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -t -c "SELECT 1 FROM pg_database WHERE datname='cognimesh';")

if [ -z "$DB_EXISTS" ]; then
    # The 'cognimesh' database does not exist, create it
    PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -c "CREATE DATABASE cognimesh WITH ENCODING 'UTF8' LC_COLLATE='en_US.utf8' LC_CTYPE='en_US.utf8';"
    # Run tablesetup.sh to create tables
    ./database/tablesetup.sh
else
    # The 'cognimesh' database exists, check if it contains any tables
    TABLE_COUNT=$(PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -d cognimesh -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    TABLE_COUNT=$(echo $TABLE_COUNT | xargs) # Trim whitespace
    if [ "$TABLE_COUNT" -eq "0" ]; then
        # The database is empty, create tables
        ./database/tablesetup.sh
    else
        # The database is not empty, ask the user if they want to back it up
        echo "The database 'cognimesh' is not empty. Do you want to backup the data first? (yes/no)"
        read BACKUP_ANSWER
        if [ "$BACKUP_ANSWER" == "yes" ]; then
            # The user wants to back up the data
            BACKUP_FILE="cognimesh_backup_$(date +%Y%m%d%H%M%S).sql"
            PGPASSWORD=$PG_PASS pg_dump -h $PG_HOST -U $PG_USER -d cognimesh > $BACKUP_FILE
            echo "Backup saved to $BACKUP_FILE."
        elif [ "$BACKUP_ANSWER" == "no" ]; then
            # The user does not want to back up the data
            echo "No backup will be performed. The database will be cleared."
            PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -d cognimesh -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
            if [ $? -eq 0 ]; then
                echo "Database cleared successfully. Now creating tables."
                ./database/tablesetup.sh
                if [ $? -ne 0 ]; then
                    echo "Error occurred while creating tables."
                    exit 1
                fi
            else
                echo "Error occurred while clearing the database."
                exit 1
            fi
        fi
    fi
fi

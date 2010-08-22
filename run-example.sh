#!/bin/bash

export PGHOST=your-pg-hostname-or-ip
export PGDATABASE=your-pg-database-name
export PGUSERNAME=your-pg-username
export PGPASSWORD=your-pg-pass
export PGBDIR=/pgbackups/

python src/pgbackup.py
cd $PGBDIR

# We don't want zero sized files
find *.dump -type f -size 0 -exec rm {} \;

# Get schema
find *.dump -type f -exec pg_restore --schema-only --no-privileges --no-acl --no-owner --file {}_schema.sql {} \;

# Get data
find *.dump -type f -exec pg_restore --data-only --no-privileges --no-acl --no-owner --file {}_data.sql {} \;

git add *.sql
git commit -a -m 'PostgreSQL Backup'

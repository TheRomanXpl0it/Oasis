#!/bin/sh
chown -R cryptodude:2000 ./data
su cryptodude -c "touch data/store.db"
su cryptodude -c "sqlite3 data/store.db < init_client.sql"
#socat TCP4-LISTEN:9122,fork,reuseaddr EXEC:'python3 /service/cry.py'
su cryptodude -c "PYTHONUNBUFFERED=1 python3 /service/cry_async.py"

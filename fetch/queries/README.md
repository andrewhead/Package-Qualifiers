# Examples

Here's a basic query for fetching queries that extend `d3`.

    python fetch_queries.py d3

Data will be fetched into a SQLite `fetcher.db` by default.
Though you can also save to a Postgres database:

    python fetch_queries.py d3 --db postgres

This command will assume that you have a `postgres-credentials.json` file in the local directory.
This can specify the username and password for logging into the local `fetcher` database.
If you want to store this JSON credentials file elsewhere you can specify the location of the file:

    python fetch_queries.py d3 --db postgres --db-creds postgres-credentials.json

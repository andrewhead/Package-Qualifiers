# Examples

Here's a basic query for fetching queries that extend seeds from file `seeds.txt`.
Each seed is listed on a separate line of `seeds.txt`.

    python fetch.py queries seeds.txt

Data will be fetched into a SQLite `fetcher.db` by default.
Though you can also save to a Postgres database:

    python fetch.py --db postgres queries seeds.txt

This command will assume that you have a `postgres-config.json` file in the local directory.
This can specify the username, password, and host for logging into the `fetcher` database.
If you want to store this config file elsewhere, you can specify the location of the file:

    python fetch.py --db postgres --db-config postgres-config.json queries seeds.txt

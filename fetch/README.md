# Examples

## Fetching typical queries

Here's a command for fetching queries that extend seeds from file `seeds.txt`.
In the `seeds.txt` file, each seed is listed on a separate line.

    python fetch.py queries seeds.txt

Data will be fetched into a SQLite `fetcher.db` by default.
Though you can also save to a Postgres database:

    python fetch.py queries seeds.txt --db postgres 

This command will assume that you have a `postgres-config.json` file in the local directory.
This can specify the username, password, and host for logging into the `fetcher` database.
If you want to store this config file elsewhere, you can specify the location of the file:

    python fetch.py queries seeds.txt --db postgres --db-config postgres-config.json

# Configuring the database

You can specify the type of database and database configuration for any fetching command.
See the options in the examples for fetching queries.

# Structure of a fetching module

A fetching module should have, at the least:
* A `configure_parser` method that takes in a subcommand parser for, and sets the command description and arguments.
* A `main` method that has the signature `main(<expected args>, *args, **kwargs)` where `<expected args>` are the arguments that you added in the `configure_parser` method

New fetching modules should be added to the `SUBMODULES` list at the top of the `fetch.py` file.
The `main` method of a fetching module can optionally be wrapped with the `lock_method(<filename>)` decorator, which enforces that the main method is only invoked once at a time.

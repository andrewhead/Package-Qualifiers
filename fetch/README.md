# Examples

## Fetch typical queries

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

# Fetch search results

To fetch search results, you will need two files.
First, a `queries.txt` file that lists one query per line.
Second, a `google-credentials.json` file.
This is a JSON file with two keys, containing the credentials you need to access search.
One key, `search_id`, is the ID of your custom search engine.
The other, `api_key`, is your Google Developer API key.

Then, you can fetch search results like this:

    python fetch.py results queries.txt google-credentials.json

By default, the program will ignore results from Stack Overflow so it can focus on fetching tutorial content.
If you want to include Stack Overflow results, use the `--include-stack-overflow` tag:

    python fetch.py results queries.txt google-credentials.json --include-stack-overflow

# Fetch webpages for search results

To get the HTML content for search results, run:

    python fetch.py results_content

This will fetch content for all pages that haven't yet been downloaded.
To fetch content for specific search results, you have a couple of options:

    python fetch.py results_content --fetch-indexes 2

for example, will fetch content for all results that are associated with a search with the 'fetch index' of 2.
You can provide a list of acceptable fetch indexes by specifying a space-delimited list of indexes on the command line.
You can also do this:

    python fetch.py results_content --fetch-all

To fetch the content for all search results retrieved so far.
This could be helpful if you want to retrieve contents for search results more than once.

# Configuring the database

You can specify the type of database and database configuration for any fetching command.
See the options in the examples for fetching queries.

# Structure of a fetching module

A fetching module should have, at the least:
* A `configure_parser` method that takes in a subcommand parser for, and sets the command description and arguments.
* A `main` method that has the signature `main(<expected args>, *args, **kwargs)` where `<expected args>` are the arguments that you added in the `configure_parser` method

New fetching modules should be added to the `SUBMODULES` list at the top of the `fetch.py` file.
The `main` method of a fetching module can optionally be wrapped with the `lock_method(<filename>)` decorator, which enforces that the main method is only invoked once at a time.

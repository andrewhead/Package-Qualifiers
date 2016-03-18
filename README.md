# Package-Qualifiers

Visualizations and representations that indicate the quality of external support for software packages.

# Examples

## Fetching data

### Fetch typical queries

Here's a command for fetching queries that extend seeds from file `seeds.txt`.
In the `seeds.txt` file, each seed is listed on a separate line.

    python data.py fetch queries seeds.txt

Data will be fetched into a SQLite `fetcher.db` by default.
Though you can also save to a Postgres database:

    python data.py fetch queries seeds.txt --db postgres 

This command will assume that you have a `postgres-config.json` file in the local directory.
This can specify the username, password, and host for logging into the `fetcher` database.
If you want to store this config file elsewhere, you can specify the location of the file:

    python data.py fetch queries seeds.txt --db postgres --db-config postgres-config.json

### Fetch search results

To fetch search results, you will need two files.
First, a `queries.txt` file that lists one query per line.
Second, a `google-credentials.json` file.
This is a JSON file with two keys, containing the credentials you need to access search.
One key, `search_id`, is the ID of your custom search engine.
The other, `api_key`, is your Google Developer API key.

Then, you can fetch search results like this:

    python data.py fetch results queries.txt google-credentials.json

By default, the program will ignore results from Stack Overflow so it can focus on fetching tutorial content.
If you want to include Stack Overflow results, use the `--include-stack-overflow` tag:

    python data.py fetch results queries.txt google-credentials.json --include-stack-overflow

### Fetch webpages for search results

To get the HTML content for search results, run:

    python data.py fetch results_content

This will fetch content for all pages that haven't yet been downloaded.
To fetch content for specific search results, you have a couple of options:

    python data.py fetch results_content --fetch-indexes 2

for example, will fetch content for all results that are associated with a search with the 'fetch index' of 2.
You can provide a list of acceptable fetch indexes by specifying a space-delimited list of indexes on the command line.
You can also do this:

    python data.py fetch results_content --fetch-all

To fetch the content for all search results retrieved so far.
This could be helpful if you want to retrieve contents for search results more than once.

## Importing data

To import Stack Overflow posts from an XML file containing posts data, run:

    python data.py import stackoverflow posts Posts.xml

For other data types (e.g., votes, users, and tags), change `posts` to the data type you want to import and `Posts.xml` to the file containing data.
See the help for the `import` subcommand for the types of data you can import.

Because importing data will take a while, you can view the progress with:

    python data.py import stackoverflow posts Posts.xml --show-progress

Though note that showing progress might yield a pretty large output log, if you are collecting one.

A Stack Overflow dump can be found on [The Internet Archive](https://archive.org/details/stackexchange).
Just like for the `fetch` commands, you can also set the `--db` and `--db-config` parameters to import the data into a specific database.

## Running this on a remote host

See the README in the `deploy` directory for instructions on how to deploy these routines to a remote host.

# Configuring the database

You can specify the type of database and database configuration for any fetching command.
See the options in the examples for fetching queries.

# Contributing

## Structure of a fetching or importing module

A module for fetching or importing a specific type of data should have, at the least:
* A `configure_parser` method that takes in a subcommand parser for, and sets the command description and arguments.
* A `main` method that has the signature `main(<expected args>, *args, **kwargs)` where `<expected args>` are the arguments that you added in the `configure_parser` method

New modules should be added to the appropriate `SUBMODULES` lists at the top of the `data.py` file.
The `main` method of a fetching module can optionally be wrapped with the `lock_method(<filename>)` decorator, which enforces that the main method is only invoked once at a time.

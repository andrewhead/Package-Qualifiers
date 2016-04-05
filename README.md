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

## Computing derived data

If you want to compute derived table based on already fetched or imported data, you can use the `compute` commands.
For example:

    python data.py compute post_tags

will compute the table that links Stack Overflow posts to their tags.
You can see a list of available computations by running `python data.py compute --help`.
Just like for the commands for fetching and importing data, you can specify your data with the `--db` and `--db-config` parameters.

If you run the `compute tasks` command, you *must* specify a `--db-config`.
The Java program that this command wraps connects only to Postgres and does not share the default database configuration of the rest of the project.

## Running migrations

If the models have been updated since you created your tables, you should run migrations on your database:

    python data.py migrate run_migration 0001_add_index_tag_excerpt_post_id

Where the last argument (`0001_add_index_tag_excerpt_post_id` in this case) is the name of the migration you want to run.
To see the available migrations, call `python data.py migrate run_migration --help`).

If you update the models, please write a migration that others can apply to their database.
See instructions in the sections below.

## Dumping data

It might be necessary to dump data to file.
You can dump special data types to file, for example:

    python data.py dump node_post_stats

This produces a file `data/dump.node_post_stats-<timestamp` in JSON format.
Run `python data.py dump -h` to see what types of data can already be dumped.
And be patient---especially when these files have to do a digest of millions of rows of a table, these scripts may take a while.

You are welcome to write your own data dumping routines.
See the "Contributing" section.

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

## Writing a migration

If you update a model, it's a necessary courtesy to others to write a migration script that will apply to existing databases to bring them up to date.

Migrations are easy to write.
First, create a Python module in the `migrate` directory.
Its file name should start with a four-digit index after the index of the last-written migration (e.g., `0007` if the last migration started with `0006`).

Then, write the forward migration procedure.
You do this by instantiating a single method called `forward`, that takes a `migrator` as its only argument.
Call Peewee `migrate` methods on this object to transform the database.
For a list of available migration methods, see the [Peewee docs](http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#schema-migrations).
This should only take a few lines of code.

We're only supporting forward migrations for now.

## Writing a data dump module

To add a script for dumping a certain type of data, decorate the `main` function of your module with `dump_json` from the `dump` module.
This decorator takes one argument: the basename of a file to save in the `data/` directory.
The `main` should do some queries to the database, and `yield` lists of records that will be saved as JSON.

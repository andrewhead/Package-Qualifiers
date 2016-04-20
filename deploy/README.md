# Deploying this Project

## Deploying to an Ubuntu machine

To deploy this project to an Ubuntu machine, run:

    ./deploy

To see the available tags, type `./deploy --tags=help`.

## Running jobs

To set up `cron` jobs for fetching data, use the `runjob` utility:

    ./runjob queries

The above example will configure the job that fetches typical queries for packages.
If your run `./runjob` without an argument, you can see a list of the available jobs.

## Configuring your deploy machine

The `deploy` script requires Ansible version 2.0 or above.
Run `pip install -U ansible` to get the latest version.

The `deploy` script sets up credentials for database login, and accesses them from S3.
You will need three sets of credentials locally.
These files are:
* `aws-credentials.json`
* `fetcher-postgres-credentials.json`
* `reader-postgres-credentials.json`

All of these files should be placed in the same directory as this `README`.
You must write the `aws-credentials.json` file by hand to reflect your Amazon Web Services credentials.
This JSON file should have these contents, substituting in your own credentials:

    {
        "aws_access_key_id": <access-key-id>,
        "aws_secret_access_key": <secret-access-key>
    }

You can find the `fetcher-pg-credentials.json` and `reader-pg-credentials.json` files on S3 storage.
Ask the project maintainer for access to these files.
These are required to configure the database with the default users and privileges.

## Data Security

The PostgreSQL server is set up without SSL communication.
This was mainly to enable getting started with the data quickly.
If the data server ever collects private or confidential data, PostgreSQL communications using this data must be reconfigured to use SSL.

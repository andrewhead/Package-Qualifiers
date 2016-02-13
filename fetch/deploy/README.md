# Notes

## Usage

To deploy this project to an Ubuntu machine, run:

    ./deploy

## Setup

The `deploy` script requires Ansible version 2.0 or above.
Run `pip install -U ansible` to get the latest version.

The `deploy` script sets up credentials for database login.
You will need two sets of credentials to enable database login---`aws-credentials.json` and `postgrest-credentials.json`.
Both of these files should be placed in the same directory as this `README`.

First, make an `aws-credentials.json` file with your Amazon Web Services credentials.
This JSON file should have these contents, substituting in your own credentials:

    {
        "aws_access_key_id": <access-key-id>,
        "aws_secret_access_key": <secret-access-key>
    }

Also, download the `postgres-credentials.json` file from S3 storage.
Ask the project maintainer for access to this file.

## Data Security

The PostgreSQL server is set up without SSL communication.
This was mainly to enable getting started with the data quickly.
If the data server ever collects private or confidential data, PostgreSQL communications using this data must be reconfigured to use SSL.

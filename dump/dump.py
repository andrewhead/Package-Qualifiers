#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import functools
from datetime import datetime
import json
import codecs
import time
import os.path


logging.basicConfig(level=logging.INFO, format="%(message)s")


def dump_json(dest_basename):
    ''' Iterate over a generator function to dump JSON records to file. '''

    def decorator(func):

        @functools.wraps(func)
        def collect_and_dump(*args, **kwargs):

            full_filename = dest_basename + time.strftime("%Y-%m-%d_%H:%M:%S") + ".json"
            dump_path = os.path.join('data', full_filename)

            with codecs.open(dump_path, 'w', encoding='utf8') as dump_file:

                dump_file.write('[\n')
                first_record = True

                for value_list in func(*args, **kwargs):
                    for record in value_list:

                        if not first_record:
                            dump_file.write(',\n')

                        # Convert non-JSON data to JSON
                        cleaned_record = {}
                        for field, value in record.items():
                            if isinstance(value, datetime):
                                cleaned_record[field] = value.isoformat()
                            else:
                                cleaned_record[field] = value

                        dump_file.write(json.dumps(cleaned_record))
                        first_record = False

                dump_file.write('\n]')

        return collect_and_dump

    return decorator

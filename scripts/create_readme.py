#!/usr/bin/env python

import json

from fep_tools import (
    data_for_json_file,
    Readme,
    INDEX_JSON_PATH,
    README_PATH,
)

with open(README_PATH, "w") as f1:
    f1.writelines(Readme().content)


with open(INDEX_JSON_PATH, "w") as index_file:
    json.dump(data_for_json_file(), index_file, indent=2)

#!/usr/bin/python

import json

from tools import index, Readme

with open("README.md", "w") as f1:
    f1.writelines(Readme().content)

with open("index.json", "w") as index_file:
    result = []
    for fep in index():
        data = fep.parsed_frontmatter
        data["title"] = fep.title
        result.append(data)
    index_file.write(json.dumps(result, indent=2))

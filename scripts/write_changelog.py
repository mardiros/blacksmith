#!/usr/bin/env python3
import datetime

import blacksmith

header = (
    f"{blacksmith.__version__}  - "
    f"Released on {datetime.datetime.now().date().isoformat()}"
)
with open("CHANGELOG.rst.new", "w") as changelog:
    changelog.write(header)
    changelog.write("\n")
    changelog.write("-" * len(header))
    changelog.write("\n")
    changelog.write("* please write here \n\n")

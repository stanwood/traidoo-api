#!/usr/bin/env python
import os
import re

import yaml


def render_yaml(file_name):
    with open(file_name) as src:
        app = yaml.load(src.read())

    for key in app["env_variables"]:
        try:
            environment_name = os.environ["ENVIRONMENT_NAME"]
            environment_value = os.environ[f"{environment_name}_{key}"]
        except KeyError:
            environment_value = os.environ.get(key, "")

        app["env_variables"][key] = str(environment_value)
        os.environ[key] = str(environment_value)  # required for deployment

    app = yaml.dump(app, default_flow_style=False)
    app = re.sub(r"\n([a-z])", r"\n\n\1", app)
    with open(file_name, "w") as dst:
        dst.write(app)


if "__main__" == __name__:

    for file_name in ("app.yaml",):
        render_yaml(file_name)

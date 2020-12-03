#!/usr/bin/env python
import os
import re

import yaml


def render_yaml(file_name):
    with open(file_name) as src:
        app = yaml.load(src.read())

    for key in app["env_variables"]:
        environment_value = os.environ.get(key, "")
        app["env_variables"][key] = str(environment_value)

    app["vpc_access_connector"][
        "name"
    ] = "projects/{project_id}/locations/{region}/connectors/{connector}".format(
        project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
        region=os.environ["GOOGLE_CLOUD_PROJECT_LOCATION"],
        connector=os.environ["REDIS_CONNECTOR"],
    )

    print(app["vpc_access_connector"]["name"])

    app = yaml.dump(app, default_flow_style=False)
    app = re.sub(r"\n([a-z])", r"\n\n\1", app)
    with open(file_name, "w") as dst:
        dst.write(app)


if "__main__" == __name__:

    for file_name in ("app.yaml",):
        render_yaml(file_name)

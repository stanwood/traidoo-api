import os
from decimal import Decimal

import jinja2

from core.calculators.utils import round_float
from core.calculators.value import Value


def format_price(value):
    value = round_float(value)
    return "{:.2f}".format(value).replace(".", ",")


def get_price_value(line):
    return Value(
        Decimal(line["price"])
        * Decimal(line["count"])
        * Decimal(line.get("amount", 1)),
        Decimal(line["vat_rate"]),
    )


def sum_lines_net_price(lines):
    return sum(
        [
            Decimal(line["price"])
            * Decimal(line["count"])
            * Decimal(line.get("amount", 1))
            for line in lines
        ]
    )


def sum_lines_vat_amount(lines):
    lines_value = [get_price_value(line) for line in lines]

    lines_sum = sum(lines_value)
    return lines_sum.vat


def setup_env():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), "templates")
        )
    )

    env.filters["format_price"] = format_price
    env.filters["price_value"] = get_price_value
    env.filters["sum_lines_net_price"] = sum_lines_net_price
    env.filters["sum_lines_vat"] = sum_lines_vat_amount

    return env


def render_template(template_path):
    # TODO: do it better
    jinja = setup_env()
    html = jinja.get_template(template_path)
    return html.render()

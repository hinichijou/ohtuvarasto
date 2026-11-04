from dataclasses import dataclass

from flask import (
    Flask,
    current_app,
    redirect,
    render_template_string,
    request,
    url_for,
)

from varasto import Varasto


@dataclass
class Warehouse:
    warehouse_id: int
    name: str
    storage: Varasto


_TEMPLATE = """
<!doctype html>
<title>Warehouses</title>
<h1>Warehouses</h1>

<form action="{{ url_for('create_warehouse') }}" method="post">
  <label for="name">Name</label>
  <input id="name" name="name" type="text">
  <label for="capacity">Capacity</label>
  <input id="capacity" name="capacity" type="text">
  <button type="submit">Create</button>
</form>

{% if warehouses %}
<ul>
{% for warehouse in warehouses %}
  <li>
    {{ warehouse.name }} | used: {{ format_number(warehouse.storage.saldo) }} | capacity: {{ format_number(warehouse.storage.tilavuus) }}
    <form action="{{ url_for('add_to_warehouse', warehouse_id=warehouse.warehouse_id) }}" method="post">
      <input name="amount" type="text">
      <button type="submit">Add</button>
    </form>
    {% if warehouse.storage.saldo > 0 %}
    <form action="{{ url_for('remove_from_warehouse', warehouse_id=warehouse.warehouse_id) }}" method="post">
      <input name="amount" type="text">
      <button type="submit">Remove</button>
    </form>
    {% endif %}
  </li>
{% endfor %}
</ul>
{% else %}
<p>No warehouses available</p>
{% endif %}
"""


def _parse_non_negative_float(value):
    try:
        parsed_value = float(value)
    except ValueError:
        return None
    if parsed_value < 0:
        return None
    return parsed_value


def _parse_warehouse_name(name):
    cleaned_name = name.strip()
    if not cleaned_name:
        return None
    if len(cleaned_name) > 50:
        return None
    if not all(character.isalnum() or character.isspace()
               for character in cleaned_name):
        return None
    return cleaned_name


def _format_number(value):
    if value.is_integer():
        return str(int(value))
    return str(value)


def _find_warehouse(warehouses, warehouse_id):
    for warehouse in warehouses:
        if warehouse.warehouse_id == warehouse_id:
            return warehouse
    return None


def index():
    return render_template_string(
        _TEMPLATE,
        warehouses=current_app.config["WAREHOUSES"],
        format_number=_format_number,
    )


def create_warehouse():
    warehouses = current_app.config["WAREHOUSES"]
    name = _parse_warehouse_name(request.form.get("name", ""))
    capacity = _parse_non_negative_float(request.form.get("capacity", ""))

    if name is None or capacity is None:
        return redirect(url_for("index"))

    if any(warehouse.name == name for warehouse in warehouses):
        return redirect(url_for("index"))

    warehouses.append(
        Warehouse(
            warehouse_id=current_app.config["NEXT_ID"],
            name=name,
            storage=Varasto(capacity),
        )
    )
    current_app.config["NEXT_ID"] += 1

    return redirect(url_for("index"))


def add_to_warehouse(warehouse_id):
    warehouse = _find_warehouse(current_app.config["WAREHOUSES"], warehouse_id)
    amount = _parse_non_negative_float(request.form.get("amount", ""))

    if warehouse is not None and amount is not None:
        warehouse.storage.lisaa_varastoon(amount)

    return redirect(url_for("index"))


def remove_from_warehouse(warehouse_id):
    warehouse = _find_warehouse(current_app.config["WAREHOUSES"], warehouse_id)
    amount = _parse_non_negative_float(request.form.get("amount", ""))

    if warehouse is not None and amount is not None:
        warehouse.storage.ota_varastosta(amount)

    return redirect(url_for("index"))


def create_app():
    flask_app = Flask(__name__)
    flask_app.config["WAREHOUSES"] = []
    flask_app.config["NEXT_ID"] = 0
    flask_app.add_url_rule("/", "index", index, methods=["GET"])
    flask_app.add_url_rule("/warehouses", "create_warehouse", create_warehouse,
                           methods=["POST"])
    flask_app.add_url_rule(
        "/warehouses/<int:warehouse_id>/add",
        "add_to_warehouse",
        add_to_warehouse,
        methods=["POST"],
    )
    flask_app.add_url_rule(
        "/warehouses/<int:warehouse_id>/remove",
        "remove_from_warehouse",
        remove_from_warehouse,
        methods=["POST"],
    )
    return flask_app


app = create_app()

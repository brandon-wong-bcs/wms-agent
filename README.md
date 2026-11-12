# Warehouse AI Assistant

A learning project with a Streamlit chat interface and a LangChain agent powered by Groq. The active assistant retrieves purchase orders and PO vendors from a configured warehouse management system (WMS), and uses helper tools for dates and calculations.

The original synthetic SQLite warehouse database remains available for learning and local experiments. The active assistant reads from the WMS API and does not use `warehouse.db`.

## Current capabilities

| Tool | Purpose | Limits |
| --- | --- | --- |
| `get_PO_list` | Search PO headers by PO number, vendor, SKU, status, type code, or date range. | Requires at least one search filter; returns up to 25 headers. Closed POs are excluded unless `includeClosed=true`. |
| `get_PO_detail` | Retrieve a PO header and its lines, including SKUs, quantities, UOMs, costs, and statuses. | Requires a positive header ID, normally obtained from `get_PO_list`; requests up to 100 lines. |
| `get_all_PO_vendor` | Search or list PO vendor codes and names for the configured warehouse and company. | Returns up to 20 vendors per batch. The agent retrieves another batch only when the user explicitly asks for more. |
| `get_datetime` | Get the current local date and time. | Uses the machine's local time. |
| `basic_calculator` | Add, subtract, multiply, or divide two numbers. | Division by zero returns an error message. |
| `calculate_percentage` | Calculate `part / total * 100`, rounded to two decimal places. | The total must be nonzero. |

The WMS client supports GET requests for warehouse data. It obtains a bearer token through a password-grant token request, caches it until shortly before expiry, and retries a WMS request once after a 401 response.

The active agent does not provide inventory, location, shipment, or receipt lookups, or change warehouse data. Older tools are stored in `tools/defunct/`; `tools/receipts.py` is currently an empty placeholder.

## Project structure

```text
Agent/
|-- main.py                       # Streamlit chat UI and session conversation history
|-- requirements.txt              # Pinned packages from the current virtual environment
|-- agent/
|   |-- wms_agent.py              # Groq model, system prompt, and registered tools
|   `-- wms_client.py             # WMS authentication and GET request helper
|-- tools/
|   |-- purchase_order.py         # PO header, detail, and vendor lookups
|   |-- helpers.py                # Date/time and calculation tools
|   |-- receipts.py               # Empty placeholder
|   `-- defunct/                  # Older, unregistered warehouse tools
|-- fields/
|   `-- purchase_order.py         # Fields retained from WMS responses
|-- database/
|   |-- create_database.py        # Create and seed the synthetic SQLite database
|   |-- upgrade_database.py       # Reapply the current schema and seed scripts
|   |-- schema.sql                # Table definitions and constraints
|   `-- seed.sql                  # Synthetic dataset
|-- docs/                         # Original SQLite inventory guides
|-- helpers/                      # API discovery and documentation utilities
|-- others/                       # Separate research-agent experiments and notes
`-- README.md
```

## Set up Python on Windows PowerShell

The current environment uses Python 3.13.15. Use Python 3.13 and, from the project root, create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```powershell
python -m pip install -r requirements.txt
```

[requirements.txt](requirements.txt) captures the installed packages and exact versions from the current `.venv` using `pip freeze`, including transitive dependencies and packages used by the research experiments. It excludes `pip` itself. After intentionally changing the environment, refresh this snapshot from the project root:

```powershell
python -m pip freeze | Set-Content -Encoding utf8 requirements.txt
```

## Configure the connection

Create a `.env` file in the project root using your own connection values:

```dotenv
GROQ_API_KEY=your-groq-api-key
WMS_BASE_URL=https://your-wms-host
WMS_TOKEN_URL=https://your-auth-host/connect/token
WMS_CLIENT_ID=your-client-id
WMS_USERNAME=your-wms-username
WMS_PASSWORD=your-wms-password
WMS_WAREHOUSE=your-warehouse-code
WMS_COMPANY=your-company-code
WMS_SCOPE=
WMS_VERIFY_SSL=true
```

`WMS_BASE_URL` is the API origin without a trailing slash; the client appends paths beginning with `/api/app/`. `WMS_TOKEN_URL` must be the full token endpoint for your installation and must support the password grant used by the client. `WMS_WAREHOUSE` scopes PO lookups, and vendor lookups also use `WMS_COMPANY`.

`WMS_SCOPE` is optional and defaults to an empty string. TLS certificate verification defaults to enabled. For a local development server with an untrusted certificate, `WMS_VERIFY_SSL=false` disables verification for both token and API requests. `.env` files are ignored by Git; keep credentials out of source files.

The Groq model is currently set to `qwen/qwen3.8-27b` in [agent/wms_agent.py](agent/wms_agent.py), with `max_tokens=800`. Your Groq account must have access to the configured model; edit that file to select another compatible model if needed.

## Run the assistant

With the virtual environment active, run from the project root:

```powershell
python -m streamlit run main.py
```

Open the address printed by Streamlit. The UI streams model responses, retains conversation history in the Streamlit session, and displays a collapsible Reasoning panel when the model returns reasoning content. Tool calls are logged in the terminal.

Example requests (replace example values with values from your WMS):

- "Find purchase order PO-12345, including closed orders."
- "Show the SKUs, ordered quantities, and pending quantities for that PO."
- "Find POs for vendor Example Supplier."
- "List PO vendors."
- "Show the next 20 vendors."

PO searches return headers; the agent needs a separate detail lookup for line information. Neither the PO list nor PO detail tool currently exposes pagination. Results can therefore be partial, and the agent is instructed to report completeness limits rather than calculate overall totals from incomplete data. Vendor lookups support paging but provide no total count; a full batch only indicates that more vendors may exist.

## Synthetic SQLite database

This separate learning dataset uses Python's built-in `sqlite3` module and needs no third-party packages or WMS credentials. Create or seed it from the project root:

```powershell
py -3.13 database\create_database.py
```

The script creates `warehouse.db` in the project root, runs `database/schema.sql` and `database/seed.sql`, and enables and checks foreign keys. Rerunning it does not duplicate the seeded rows. To recreate a blank database, close any program using it, delete `warehouse.db`, and run the command again. `database/upgrade_database.py` reapplies the same schema and seed scripts to an existing database; it is not a versioned migration system.

The schema now includes:

- **Products**: SKU, product name, and counting unit.
- **Locations**: location ID, zone, and operational type.
- **Inventory**: quantity and status for a product at a location.
- **ShipmentOrders** and **ShipmentLines**: shipment headers and their SKU quantities.
- **Allocations**: links between shipment lines, inventory, and warehouse locations, with allocation and picking fields.

Inspect it with a SQLite viewer or a quick query:

```powershell
py -3.13 -c "import sqlite3; db=sqlite3.connect('warehouse.db'); print(db.execute('SELECT * FROM Inventory').fetchall()); db.close()"
```

The original [database guide](docs/database.md), [product guide](docs/products.md), [location guide](docs/locations.md), and [inventory guide](docs/inventory.md) cover the synthetic inventory portion of the schema.

## Development utilities

- `helpers/swagger_to_csv.py` exports API endpoints, parameters, and response fields from an OpenAPI document. It includes GET endpoints by default and supports `--filter`, `--out`, and `--all-methods`.
- `helpers/get _models.py` lists models returned by Groq using `GROQ_API_KEY`.
- `helpers/generate_tool_docs.py` is an unfinished tool-reference generator: it currently imports a `tools` collection that `tools/__init__.py` does not define.

For example, export purchase-related endpoints from a local OpenAPI file:

```powershell
python helpers\swagger_to_csv.py --file path\to\swagger.json --filter purchase --out helpers\wms_endpoints.csv
```

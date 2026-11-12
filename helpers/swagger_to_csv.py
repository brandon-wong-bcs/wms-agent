"""
swagger_to_csv.py - List WMS API endpoints and the fields they return.

Usage (PowerShell):
    # From the running app (add a token if Swagger needs login)
    python swagger_to_csv.py --url https://localhost:44300/swagger/v1/swagger.json --insecure
    python swagger_to_csv.py --url https://wms-host/swagger/v1/swagger.json --token "eyJhbGciOi..."

    # From a file you saved from the browser
    python swagger_to_csv.py --file swagger.json

    # Include POST/PUT/DELETE too (default is GET only)
    python swagger_to_csv.py --file swagger.json --all-methods

    # Only endpoints whose path contains a word
    python swagger_to_csv.py --file swagger.json --filter purchase

Output: wms_endpoints.csv (open in Excel)
"""

import argparse
import csv
import json
import sys

MAX_DEPTH = 2  # how many levels of nested DTOs to expand (e.g. PO -> Lines)


# ---------- loading ----------

def load_spec(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return json.load(f)

    import requests
    if args.insecure:
        import urllib3
        urllib3.disable_warnings()  # local dev certificates
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    resp = requests.get(args.url, headers=headers, verify=not args.insecure, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ---------- schema helpers ----------

def short_name(ref):
    """'#/components/schemas/BLS.Wms.PurchaseOrders.PurchaseOrderDetailDto' -> 'PurchaseOrderDetailDto'.
    Also shortens ABP generic names like PagedResultDto`1[[...ItemDto, ...]]."""
    name = ref.split("/")[-1]
    if "[[" in name:  # generic: Outer`1[[Inner, Assembly]]
        outer = name.split("`")[0].split(".")[-1]
        inner = name.split("[[", 1)[1].split(",")[0].split(".")[-1]
        return f"{outer}<{inner}>"
    return name.split(".")[-1]


def resolve(schema, schemas):
    """Follow $ref / allOf so we get to the real object definition."""
    seen = 0
    while schema and seen < 10:
        seen += 1
        if "$ref" in schema:
            schema = schemas.get(schema["$ref"].split("/")[-1], {})
        elif "allOf" in schema and len(schema["allOf"]) == 1:
            schema = schema["allOf"][0]
        else:
            break
    return schema or {}


def type_label(schema):
    """Human-readable type: string, int32, List[LineDto], LineDto, ..."""
    if not schema:
        return ""
    if "$ref" in schema:
        return short_name(schema["$ref"])
    if "allOf" in schema and schema["allOf"]:
        return type_label(schema["allOf"][0])
    t = schema.get("type", "object")
    if t == "array":
        return f"List[{type_label(schema.get('items', {}))}]"
    fmt = schema.get("format")
    if schema.get("enum"):
        return "enum"
    return fmt if fmt in ("int32", "int64", "date-time", "uuid", "double") else t


def describe_fields(schema, schemas, depth=0):
    """Return 'field:type, field:type{nested...}' for an object schema."""
    obj = resolve(schema, schemas)
    if obj.get("type") == "array":
        return describe_fields(obj.get("items", {}), schemas, depth)
    props = obj.get("properties", {})
    parts = []
    for name, prop in props.items():
        label = f"{name}:{type_label(prop)}"
        # expand nested objects / lists of objects
        inner = prop.get("items", prop) if prop.get("type") == "array" else prop
        if depth < MAX_DEPTH and ("$ref" in inner or "allOf" in inner):
            nested = describe_fields(inner, schemas, depth + 1)
            if nested:
                label += "{" + nested + "}"
        parts.append(label)
    return ", ".join(parts)


def row_dto(schema, schemas):
    """For paged results ({items: [...], totalCount}) return the row DTO name."""
    obj = resolve(schema, schemas)
    items = obj.get("properties", {}).get("items")
    if items and items.get("type") == "array":
        return type_label(items.get("items", {}))
    return ""


def response_schema(op):
    for code in ("200", "201", "204"):
        resp = op.get("responses", {}).get(code)
        if resp:
            content = resp.get("content", {})
            for media in ("application/json", "text/json", "text/plain"):
                if media in content:
                    return content[media].get("schema", {})
            if content:
                return next(iter(content.values())).get("schema", {})
            return {}
    return {}


def describe_params(op, spec_params):
    names = []
    for p in op.get("parameters", []):
        if "$ref" in p:
            p = spec_params.get(p["$ref"].split("/")[-1], {})
        req = "*" if p.get("required") else ""
        names.append(f"{p.get('name')}{req}({p.get('in')})")
    if "requestBody" in op:
        content = op["requestBody"].get("content", {})
        schema = next(iter(content.values()), {}).get("schema", {}) if content else {}
        names.append(f"body:{type_label(schema)}")
    return ", ".join(names)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="Export Swagger endpoints to CSV")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="swagger.json URL")
    src.add_argument("--file", help="local swagger.json file")
    ap.add_argument("--token", help="bearer token, if Swagger needs login")
    ap.add_argument("--insecure", action="store_true", help="skip HTTPS certificate check (local dev only)")
    ap.add_argument("--all-methods", action="store_true", help="include POST/PUT/PATCH/DELETE")
    ap.add_argument("--filter", help="only paths containing this text (case-insensitive)")
    ap.add_argument("--out", default="wms_endpoints.csv")
    args = ap.parse_args()

    spec = load_spec(args)
    if "paths" not in spec:
        sys.exit("This doesn't look like a Swagger/OpenAPI file (no 'paths').")

    schemas = spec.get("components", {}).get("schemas", {})
    spec_params = spec.get("components", {}).get("parameters", {})
    methods = {"get", "post", "put", "patch", "delete"} if args.all_methods else {"get"}

    rows = []
    for path, ops in spec["paths"].items():
        if args.filter and args.filter.lower() not in path.lower():
            continue
        for method, op in ops.items():
            if method.lower() not in methods:
                continue
            schema = response_schema(op)
            rows.append({
                "service": ", ".join(op.get("tags", [])),
                "method": method.upper(),
                "path": path,
                "operation": op.get("operationId", ""),
                "params (*=required)": describe_params(op, spec_params),
                "returns": type_label(schema),
                "row_dto (paged lists)": row_dto(schema, schemas),
                "fields": describe_fields(schema, schemas),
            })

    if not rows:
        sys.exit("No matching endpoints found.")

    rows.sort(key=lambda r: (r["service"], r["path"], r["method"]))
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig opens cleanly in Excel
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    services = len({r["service"] for r in rows})
    print(f"{len(rows)} endpoints across {services} services written to {args.out}")


if __name__ == "__main__":
    main()

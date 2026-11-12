from tools import tools


lines = ["# WMS Agent Tools", ""]

for tool in tools:
    lines.append(f"## `{tool.name}`")
    lines.append("")
    lines.append(tool.description.strip())
    lines.append("")
    lines.append("### Parameters")
    lines.append("")

    schema = tool.args_schema.model_json_schema()
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    if not properties:
        lines.append("This tool has no parameters.")
        lines.append("")
        continue

    lines.append("| Parameter | Type | Required | Description |")
    lines.append("|---|---|---|---|")

    for name, info in properties.items():
        parameter_type = info.get("type", "unknown")
        required = "Yes" if name in required_fields else "No"
        description = info.get("description", "")

        lines.append(
            f"| `{name}` | {parameter_type} | {required} | {description} |"
        )

    lines.append("")


with open("TOOLS.md", "w", encoding="utf-8") as file:
    file.write("\n".join(lines))


print(f"Generated TOOLS.md containing {len(tools)} tools.")
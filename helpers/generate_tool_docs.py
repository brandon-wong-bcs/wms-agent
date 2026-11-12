"""Generate TOOLS.md from the WMS agent's registered tools."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def render_tool_docs(registered_tools):
    """Render tool descriptions and argument schemas as Markdown."""
    lines = ["# WMS Agent Tools", ""]

    for tool in registered_tools:
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
            description = " ".join(info.get("description", "").splitlines())
            description = description.replace("|", "\\|")

            lines.append(
                f"| `{name}` | {parameter_type} | {required} | {description} |"
            )

        lines.append("")

    return "\n".join(lines)


def main():
    # Direct execution adds helpers/ to sys.path, rather than the project root.
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from tools import tools

    output_path = PROJECT_ROOT / "TOOLS.md"
    output_path.write_text(render_tool_docs(tools), encoding="utf-8")
    print(f"Generated {output_path} containing {len(tools)} tools.")


if __name__ == "__main__":
    main()

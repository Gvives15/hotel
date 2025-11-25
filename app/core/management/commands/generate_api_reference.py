import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Genera un archivo Markdown con la referencia de la API a partir del esquema OpenAPI de Django Ninja"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="docs/API_REFERENCE.md",
            help="Ruta de salida para el archivo de referencia (por defecto docs/API_REFERENCE.md)",
        )
        parser.add_argument(
            "--base-url",
            type=str,
            default="http://localhost:8000",
            help="URL base que se usará en los ejemplos (sin la ruta del endpoint)",
        )

    def handle(self, *args, **options):
        from config.urls import api

        schema = api.get_openapi_schema()
        components = schema.get("components", {}).get("schemas", {})
        output_path = Path(options["output"])
        base_url = options["base_url"].rstrip("/")

        lines: List[str] = []
        lines.append("# API Reference")
        lines.append("")
        lines.append("Documento generado automáticamente a partir del esquema OpenAPI de Django Ninja.")
        lines.append(f"Fecha de generación: {now().strftime('%Y-%m-%d %H:%M %Z')}\n")
        lines.append(f"URL base usada en ejemplos: `{base_url}`\n")
        lines.append("> Ejecuta `python manage.py generate_api_reference --base-url <URL>` para regenerar este archivo.\n")

        auth_overrides = {
            ("get", "/api/superadmin/kpis"): "Requiere usuario autenticado con rol de superusuario.",
            ("get", "/api/superadmin/chart"): "Requiere usuario autenticado con rol de superusuario.",
            ("get", "/api/superadmin/hotels"): "Requiere usuario autenticado con rol de superusuario.",
        }

        for path in sorted(schema.get("paths", {})):
            methods = schema["paths"][path]
            for method in sorted(methods):
                operation = methods[method]
                lines.extend(self.render_operation(
                    path,
                    method,
                    operation,
                    components,
                    base_url,
                    auth_overrides.get((method, path)),
                ))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Referencia generada en {output_path}"))

    def render_operation(
        self,
        path: str,
        method: str,
        operation: Dict[str, Any],
        components: Dict[str, Any],
        base_url: str,
        auth_override: Optional[str],
    ) -> List[str]:
        title = operation.get("summary") or operation.get("description") or "Sin descripción"
        lines: List[str] = []
        lines.append(f"## {method.upper()} {path}")
        lines.append("")
        lines.append(f"**Descripción:** {title}")
        tags = operation.get("tags", [])
        if tags:
            lines.append(f"**Tags:** {', '.join(tags)}")
        security = operation.get("security") or []
        if auth_override:
            auth_text = auth_override
        elif security:
            auth_text = "Requiere autenticación configurada en la API."
        else:
            auth_text = "No requiere autenticación explícita."
        lines.append(f"**Autenticación y roles:** {auth_text}")

        parameters = operation.get("parameters", [])
        request_body = operation.get("requestBody")
        lines.append("")
        lines.append("### Parámetros")
        if not parameters and not request_body:
            lines.append("Este endpoint no requiere parámetros de entrada.")
        else:
            if parameters:
                lines.append("**Query/Path parameters**")
                for param in parameters:
                    schema = param.get("schema", {})
                    param_type = self.describe_type(schema)
                    required = "(requerido)" if param.get("required") else "(opcional)"
                    description = param.get("description", "")
                    lines.append(f"- `{param['name']}` {required} — {param_type}. {description}")
            if request_body:
                body_schema = self.resolve_schema(
                    request_body.get("content", {})
                    .get("application/json", {})
                    .get("schema", {}),
                    components,
                )
                lines.append("")
                lines.append("**Cuerpo (JSON)**")
                lines.extend(self.describe_schema_properties(body_schema))

        responses = operation.get("responses", {})
        lines.append("")
        lines.append("### Respuestas")
        if not responses:
            lines.append("No se definieron respuestas en el esquema.")
        else:
            for status, response in sorted(responses.items()):
                description = response.get("description", "")
                lines.append(f"- **{status}**: {description}")
                content = response.get("content", {})
                schema = content.get("application/json", {}).get("schema")
                if schema:
                    resolved = self.resolve_schema(schema, components)
                    lines.extend(self.describe_schema_properties(resolved, indent=2))

        lines.append("")
        lines.append("### Ejemplos")
        example_query = self.build_query_string(parameters)
        example_path = self.build_path_with_placeholders(path, parameters)
        example_url = f"{base_url}{example_path}{example_query}"
        body_payload = self.build_example_body(request_body, components)
        if method.lower() == "get":
            lines.append(f"curl -X GET \"{example_url}\"")
            lines.append(f"http GET {example_url}")
        else:
            json_body = json.dumps(body_payload, ensure_ascii=False, indent=2) if body_payload else "{}"
            lines.append(f"curl -X {method.upper()} \"{example_url}\" \\")
            lines.append("  -H 'Content-Type: application/json' \\")
            lines.append(f"  -d '{json_body}'")
            lines.append("")
            lines.append(f"http {method.upper()} {example_url} \\")
            if body_payload:
                for key, value in body_payload.items():
                    lines.append(f"  {key}={self.httpie_value(value)} \\")
                lines[-1] = lines[-1].rstrip(" \\")
            else:
                lines[-1] = lines[-1].rstrip(" \\")

        lines.append("")
        lines.append("### Respuestas de error comunes")
        error_items = self.common_errors(method, path, security or auth_override)
        for item in error_items:
            lines.append(f"- {item}")

        lines.append("")
        return lines

    def describe_type(self, schema: Dict[str, Any]) -> str:
        schema_type = schema.get("type", "object")
        fmt = schema.get("format")
        if fmt:
            return f"{schema_type} ({fmt})"
        return schema_type

    def resolve_schema(self, schema: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
        if not schema:
            return {}
        ref = schema.get("$ref")
        if ref:
            key = ref.split("/")[-1]
            return components.get(key, {})
        return schema

    def describe_schema_properties(self, schema: Dict[str, Any], indent: int = 0) -> List[str]:
        lines: List[str] = []
        prefix = " " * indent
        if not schema:
            lines.append(f"{prefix}- Sin esquema definido")
            return lines
        schema_type = schema.get("type", "object")
        if schema_type != "object" or "properties" not in schema:
            lines.append(f"{prefix}- Tipo: {self.describe_type(schema)}")
            return lines
        required = schema.get("required", [])
        for name, prop in schema.get("properties", {}).items():
            prop_type = self.describe_type(prop)
            marker = "(requerido)" if name in required else "(opcional)"
            description = prop.get("description", "")
            lines.append(f"{prefix}- `{name}` {marker}: {prop_type}. {description}")
        return lines

    def build_query_string(self, parameters: List[Dict[str, Any]]) -> str:
        query_params = [p for p in parameters if p.get("in") == "query"]
        if not query_params:
            return ""
        parts = []
        for param in query_params:
            value = self.sample_value(param.get("schema", {}), param["name"])
            parts.append(f"{param['name']}={value}")
        return "?" + "&".join(parts)

    def build_path_with_placeholders(self, path: str, parameters: List[Dict[str, Any]]) -> str:
        result = path
        for param in parameters:
            if param.get("in") == "path":
                result = result.replace(f"{{{param['name']}}}", f"<{param['name']}>")
        return result

    def build_example_body(
        self,
        request_body: Optional[Dict[str, Any]],
        components: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not request_body:
            return {}
        schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})
        resolved = self.resolve_schema(schema, components)
        if resolved.get("type") != "object":
            return {"value": self.sample_value(resolved, "dato")}
        payload = {}
        for name, prop in resolved.get("properties", {}).items():
            payload[name] = self.sample_value(prop, name)
        return payload

    def sample_value(self, schema: Dict[str, Any], name: str) -> Any:
        schema_type = schema.get("type", "string")
        fmt = schema.get("format")
        if schema_type == "integer":
            return 1
        if schema_type == "number":
            return 99.9
        if schema_type == "boolean":
            return True
        if fmt == "date":
            return "2024-01-01"
        if fmt == "email":
            return "user@example.com"
        if name.lower().startswith("fecha"):
            return "2024-01-01"
        if name.lower().startswith("email"):
            return "usuario@correo.com"
        if name.lower().startswith("dni"):
            return "12345678"
        if name.lower().startswith("id"):
            return 1
        return "texto"

    def httpie_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return f"\"{value}\""

    def common_errors(self, method: str, path: str, has_security: Any) -> List[str]:
        errors = [
            "400: Solicitud inválida o datos incompletos.",
            "422: Error de validación en los datos enviados.",
            "500: Error interno del servidor.",
        ]
        if has_security:
            errors.insert(0, "403: Acceso denegado por falta de permisos o rol insuficiente.")
        if "{" in path:
            errors.append("404: Recurso no encontrado si el identificador no existe.")
        return errors

"""
Utilities for API contract validation and testing.

This module provides helper functions for validating API responses against
OpenAPI specifications and ensuring contract compliance.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import RefResolver, validate


class ContractValidator:
    """Validates API responses against OpenAPI contract specifications."""

    def __init__(self, contract_path: str | Path) -> None:
        """Initialize the validator with a contract specification.

        Args:
            contract_path: Path to the OpenAPI specification JSON file
        """
        self.contract_path = Path(contract_path)
        with self.contract_path.open(encoding="utf-8") as f:
            self.contract = json.load(f)

        # Create a resolver for handling $ref references
        self.resolver = RefResolver(
            base_uri=f"file://{self.contract_path.absolute()}", referrer=self.contract
        )

    def validate_response(
        self, response_data: Mapping[str, Any], path: str, method: str, status_code: int
    ) -> None:
        """Validate a response against the contract schema.

        Args:
            response_data: The actual response data to validate
            path: The API path (e.g., "/api/v1/client/agents/{id}")
            method: The HTTP method (e.g., "get", "post")
            status_code: The HTTP status code (e.g., 200, 404)

        Raises:
            ValidationError: If the response doesn't match the schema
            KeyError: If the schema is not found in the contract
        """
        try:
            # Get the schema for this endpoint and status code
            endpoint_spec = self.contract["paths"][path][method.lower()]
            response_spec = endpoint_spec["responses"][str(status_code)]

            if (
                "content" in response_spec
                and "application/json" in response_spec["content"]
            ):
                schema = response_spec["content"]["application/json"]["schema"]

                # Validate the response data using the resolver for $ref handling
                validate(instance=response_data, schema=schema, resolver=self.resolver)

        except KeyError as e:
            raise KeyError(
                f"Schema not found for {method.upper()} {path} {status_code}: {e}"
            ) from e

    def validate_request(
        self, request_data: Mapping[str, Any], path: str, method: str
    ) -> None:
        """Validate a request against the contract schema.

        Args:
            request_data: The request data to validate
            path: The API path (e.g., "/api/v1/client/agents/{id}")
            method: The HTTP method (e.g., "get", "post")

        Raises:
            ValidationError: If the request doesn't match the schema
            KeyError: If the schema is not found in the contract
        """
        try:
            endpoint_spec = self.contract["paths"][path][method.lower()]

            if "requestBody" in endpoint_spec:
                request_spec = endpoint_spec["requestBody"]
                if (
                    "content" in request_spec
                    and "application/json" in request_spec["content"]
                ):
                    schema = request_spec["content"]["application/json"]["schema"]

                    # Validate the request data
                    validate(
                        instance=request_data, schema=schema, resolver=self.resolver
                    )

        except KeyError as e:
            raise KeyError(
                f"Request schema not found for {method.upper()} {path}: {e}"
            ) from e

    def get_required_fields(
        self, path: str, method: str, status_code: int
    ) -> list[str]:
        """Get the list of required fields for a response schema.

        Args:
            path: The API path
            method: The HTTP method
            status_code: The HTTP status code

        Returns:
            List of required field names
        """
        try:
            endpoint_spec = self.contract["paths"][path][method.lower()]
            response_spec = endpoint_spec["responses"][str(status_code)]

            if (
                "content" in response_spec
                and "application/json" in response_spec["content"]
            ):
                schema = response_spec["content"]["application/json"]["schema"]

                # Resolve $ref if present
                if "$ref" in schema:
                    _, resolved_schema = self.resolver.resolve(schema["$ref"])
                    schema = resolved_schema

                return schema.get("required", [])
            return []  # No JSON content found

        except KeyError:
            return []

    def get_enum_values(
        self, path: str, method: str, status_code: int, field_name: str
    ) -> list[str] | None:
        """Get the allowed enum values for a specific field.

        Args:
            path: The API path
            method: The HTTP method
            status_code: The HTTP status code
            field_name: The name of the field to check

        Returns:
            List of allowed enum values, or None if not an enum field
        """
        try:
            endpoint_spec = self.contract["paths"][path][method.lower()]
            response_spec = endpoint_spec["responses"][str(status_code)]

            if (
                "content" in response_spec
                and "application/json" in response_spec["content"]
            ):
                schema = response_spec["content"]["application/json"]["schema"]

                # Resolve $ref if present
                if "$ref" in schema:
                    _, resolved_schema = self.resolver.resolve(schema["$ref"])
                    schema = resolved_schema

                if "properties" in schema and field_name in schema["properties"]:
                    field_schema = schema["properties"][field_name]
                    return field_schema.get("enum")
                return None  # Field not found in schema properties
            return None  # No JSON content found

        except KeyError:
            return None

    def get_all_endpoints(self) -> list[dict[str, str]]:
        """Get a list of all endpoints defined in the contract.

        Returns:
            List of dictionaries with 'path' and 'method' keys
        """
        endpoints = []
        for path, path_spec in self.contract["paths"].items():
            methods_to_add = [
                {"path": path, "method": method.upper()}
                for method in path_spec
                if method != "parameters"  # Skip non-method keys
            ]
            endpoints.extend(methods_to_add)
        return endpoints

    def get_endpoint_summary(self, path: str, method: str) -> str | None:
        """Get the summary description for an endpoint.

        Args:
            path: The API path
            method: The HTTP method

        Returns:
            The endpoint summary, or None if not found
        """
        try:
            endpoint_spec = self.contract["paths"][path][method.lower()]
            return endpoint_spec.get("summary")
        except KeyError:
            return None


def validate_agent_api_v1_response(
    response_data: Mapping[str, Any], path: str, method: str, status_code: int
) -> None:
    """Convenience function to validate Agent API v1 responses.

    Args:
        response_data: The response data to validate
        path: The API path
        method: The HTTP method
        status_code: The HTTP status code

    Raises:
        ValidationError: If validation fails
    """
    contract_path = (
        Path(__file__).parent.parent.parent / "contracts" / "v1_api_swagger.json"
    )
    validator = ContractValidator(contract_path)
    validator.validate_response(response_data, path, method, status_code)


def validate_agent_api_v1_request(
    request_data: Mapping[str, Any], path: str, method: str
) -> None:
    """Convenience function to validate Agent API v1 requests.

    Args:
        request_data: The request data to validate
        path: The API path
        method: The HTTP method

    Raises:
        ValidationError: If validation fails
    """
    contract_path = (
        Path(__file__).parent.parent.parent / "contracts" / "v1_api_swagger.json"
    )
    validator = ContractValidator(contract_path)
    validator.validate_request(request_data, path, method)


def get_agent_api_v1_validator() -> ContractValidator:
    """Get a ContractValidator instance for Agent API v1.

    Returns:
        ContractValidator instance for the Agent API v1 contract
    """
    contract_path = (
        Path(__file__).parent.parent.parent / "contracts" / "v1_api_swagger.json"
    )
    return ContractValidator(contract_path)

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Any,
    Dict,
    Final,
    List,
    Literal,
    Mapping,
    TypeVar,
)

from pydantic.json_schema import GenerateJsonSchema

T = TypeVar("T", Dict, List, object)


class FmuSchemas:
    """These URLs can be constructed programmatically from radixconfig.yaml if need be:

        {cfg.components[].name}-{cfg.metadata.name}-{spec.environments[].name}

    As they are unlikely to change they are hardcoded here.
    """

    DEV_URL: Final[str] = "https://main-fmu-schemas-dev.radix.equinor.com"
    PROD_URL: Final[str] = "https://main-fmu-schemas-prod.radix.equinor.com"
    PATH: Final[Path] = Path("schemas")


class GenerateJsonSchemaBase(GenerateJsonSchema):
    """Implements a schema generator so that some additional fields may be
    added.

    This class also collects static methods used to transform the default OpenAPI
    schemas generated by Pydantic into schemas compatible with JSON Schema specs."""

    @staticmethod
    def remove_discriminator_mapping(data: T) -> T:
        """
        Removes entries with key ["discriminator"]["mapping"] from the schema. This
        adjustment is necessary because JSON Schema does not recognize this value
        while OpenAPI does.
        """

        if isinstance(data, dict):
            if "discriminator" in data and isinstance(data["discriminator"], dict):
                data["discriminator"].pop("mapping", None)

            for key, value in data.items():
                data[key] = GenerateJsonSchemaBase.remove_discriminator_mapping(value)

        elif isinstance(data, list):
            for index, element in enumerate(data):
                data[index] = GenerateJsonSchemaBase.remove_discriminator_mapping(
                    element
                )

        return data

    @staticmethod
    def remove_format_path(data: T) -> T:
        """
        Removes entries with key ["format"] = "path" from the schema. This
        adjustment is necessary because JSON Schema does not recognize the "format":
        "path", while OpenAPI does. This function is used in contexts where OpenAPI
        specifications are not applicable.
        """

        if isinstance(data, dict):
            return {
                k: GenerateJsonSchemaBase.remove_format_path(v)
                for k, v in data.items()
                if not (k == "format" and v == "path")
            }

        if isinstance(data, list):
            return [
                GenerateJsonSchemaBase.remove_format_path(element) for element in data
            ]

        return data

    def generate(
        self,
        schema: Mapping[str, Any],
        mode: Literal["validation", "serialization"] = "validation",
    ) -> dict[str, Any]:
        json_schema = super().generate(schema, mode=mode)

        json_schema = GenerateJsonSchemaBase.remove_discriminator_mapping(json_schema)
        json_schema = GenerateJsonSchemaBase.remove_format_path(json_schema)
        json_schema["$schema"] = self.schema_dialect

        return json_schema


class SchemaBase(ABC):
    VERSION: str
    """The current version of the schema."""

    FILENAME: str
    """The filename, i.e. schema.json."""

    PATH: Path
    """The on-disk _and_ URL path following the domain, i.e:

        schemas/0.1.0/schema.json

    This path should _always_ have `FmuSchemas.PATH` as its first parent.
    This determines the on-disk and URL location of this schema file. A
    trivial example is:

        PATH: Path = FmuSchemas.PATH / VERSION / FILENAME

    """

    @classmethod
    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        super().__init_subclass__(**kwargs)
        for attr in ("VERSION", "FILENAME", "PATH"):
            if not hasattr(cls, attr):
                raise TypeError(f"Subclass {cls.__name__} must define '{attr}'")

        if not cls.PATH.parts[0].startswith(str(FmuSchemas.PATH)):
            raise ValueError(
                f"PATH must start with `FmuSchemas.PATH`: {FmuSchemas.PATH}. "
                f"Got {cls.PATH}"
            )

    @classmethod
    def url(cls) -> str:
        """Returns the URL this file will reside at, based upon class variables set here
        and in FmuSchemas."""
        DEV_URL = f"{FmuSchemas.DEV_URL}/{cls.PATH}"
        PROD_URL = f"{FmuSchemas.PROD_URL}/{cls.PATH}"

        if os.environ.get("DEV_SCHEMA", False):
            return DEV_URL
        return PROD_URL

    @classmethod
    def default_generator(cls) -> type[GenerateJsonSchema]:
        """Provides a default schema generator that should be adequate for most simple
        schemas.

        When more customization is required a separate schema generator may be
        warranted. See the 'FmuResults' model for how this can be done."""

        class DefaultGenerateJsonSchema(GenerateJsonSchemaBase):
            """Implements a schema generator so that some additional fields may be
            added."""

            def generate(
                self,
                schema: Mapping[str, Any],
                mode: Literal["validation", "serialization"] = "validation",
            ) -> dict[str, Any]:
                json_schema = super().generate(schema, mode=mode)

                json_schema["$id"] = cls.url()
                json_schema["version"] = cls.VERSION

                return json_schema

        return DefaultGenerateJsonSchema

    @classmethod
    @abstractmethod
    def dump(cls) -> dict[str, Any]:
        """
        Dumps the export root model to JSON format for schema validation and
        usage in FMU data structures.

        To update the schema:
            1. Run the following CLI command to dump the updated schema:
                `./tools/update_schema --diff`.
            2. Check the diff for changes. Adding fields usually indicates non-breaking
                changes and is generally safe. However, if fields are removed, it could
                indicate breaking changes that may affect dependent systems. Perform a
                quality control (QC) check to ensure these changes do not break existing
                implementations.
                If changes are satisfactory and do not introduce issues, commit
                them to maintain schema consistency.
        """
        raise NotImplementedError
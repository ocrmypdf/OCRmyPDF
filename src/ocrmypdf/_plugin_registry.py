# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Plugin option registry for dynamic model composition."""

from __future__ import annotations

import logging

from pydantic import BaseModel

log = logging.getLogger(__name__)


class PluginOptionRegistry:
    """Registry for plugin option models.

    This registry collects option models from plugins during initialization.
    Plugin options can be accessed via nested namespaces on OcrOptions
    (e.g., options.tesseract.timeout) or via flat field names for backward
    compatibility (e.g., options.tesseract_timeout).
    """

    def __init__(self):
        self._option_models: dict[str, type[BaseModel]] = {}

    def register_option_model(
        self, namespace: str, model_class: type[BaseModel]
    ) -> None:
        """Register a plugin's option model.

        Args:
            namespace: The namespace for the plugin options (e.g., 'tesseract')
            model_class: The Pydantic model class for the plugin options
        """
        if namespace in self._option_models:
            log.warning(
                f"Plugin option namespace '{namespace}' already registered, overriding"
            )

        self._option_models[namespace] = model_class

        log.debug(
            f"Registered plugin option model for namespace '{namespace}': "
            f"{model_class.__name__}"
        )

    def get_registered_models(self) -> dict[str, type[BaseModel]]:
        """Get all registered plugin option models."""
        return self._option_models.copy()

# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Plugin option registry for dynamic model composition."""

from __future__ import annotations

import logging
from typing import Any, Dict, Type

from pydantic import BaseModel, create_model

log = logging.getLogger(__name__)


class PluginOptionRegistry:
    """Registry for plugin option models."""
    
    def __init__(self):
        self._option_models: Dict[str, Type[BaseModel]] = {}
        self._extended_model_cache: Type[BaseModel] | None = None
    
    def register_option_model(self, namespace: str, model_class: Type[BaseModel]) -> None:
        """Register a plugin's option model.
        
        Args:
            namespace: The namespace for the plugin options (e.g., 'tesseract')
            model_class: The Pydantic model class for the plugin options
        """
        if namespace in self._option_models:
            log.warning(f"Plugin option namespace '{namespace}' already registered, overriding")
        
        self._option_models[namespace] = model_class
        # Clear cache when new models are registered
        self._extended_model_cache = None
        
        log.debug(f"Registered plugin option model for namespace '{namespace}': {model_class.__name__}")
    
    def get_registered_models(self) -> Dict[str, Type[BaseModel]]:
        """Get all registered plugin option models."""
        return self._option_models.copy()
    
    def get_extended_options_model(self, base_model: Type[BaseModel]) -> Type[BaseModel]:
        """Create an extended options model that includes all registered plugin options.
        
        Args:
            base_model: The base OCROptions model to extend
            
        Returns:
            A new model class that includes the base model fields plus all plugin option fields
        """
        if self._extended_model_cache is not None:
            return self._extended_model_cache
        
        # Start with base model fields
        model_fields = {}
        
        # Add plugin option models as nested fields
        for namespace, model_class in self._option_models.items():
            model_fields[namespace] = (model_class, model_class())
        
        # Create the extended model
        self._extended_model_cache = create_model(
            'ExtendedOCROptions',
            __base__=base_model,
            **model_fields
        )
        
        return self._extended_model_cache
    
    def clear_cache(self) -> None:
        """Clear the extended model cache."""
        self._extended_model_cache = None

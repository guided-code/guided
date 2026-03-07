#!/usr/bin/env python3
"""Test script to verify the configuration module works correctly."""

import tempfile
from pathlib import Path

from guided.config.manager import ConfigManager


def test_config_creation():
    """Test that we can create and manage configurations."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".guided"
        config_manager = ConfigManager(config_dir=config_dir)

        # Load config (should create default)
        config = config_manager.load_config()
        print("Default config loaded successfully")
        print(f"Version: {config.version}")
        print(f"Logging level: {config.logging_level}")
        print(f"Models count: {len(config.models)}")

        # Test adding a new model
        new_model = {"provider": "openai", "model_name": "gpt-4", "api_key": "test-key"}
        config_manager.add_model_config(new_model)

        # Reload config to see the change
        updated_config = config_manager.load_config()
        print(f"Updated models count: {len(updated_config.models)}")

        # Verify the model was added
        if len(updated_config.models) > 1:
            print(
                f"Added model: {updated_config.models[1].provider} - {updated_config.models[1].model_name}"
            )

        print("Configuration test completed successfully!")


if __name__ == "__main__":
    test_config_creation()

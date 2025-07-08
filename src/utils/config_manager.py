"""
Configuration Manager
Handles loading and managing application configuration from YAML files
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file. If None, uses default path.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Get the project root directory
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        config_file = project_root / "config" / "config.yaml"
        
        if not config_file.exists():
            # Try template file
            template_file = project_root / "config" / "config.template.yaml"
            if template_file.exists():
                raise FileNotFoundError(
                    f"Config file not found. Please copy {template_file} to {config_file} "
                    "and update with your settings."
                )
            else:
                raise FileNotFoundError(f"No configuration file found at {config_file}")
        
        return str(config_file)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Override with environment variables if they exist
            config = self._override_with_env_vars(config)
            
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        # Database configuration
        if 'POSTGRES_HOST' in os.environ:
            config.setdefault('database', {})['host'] = os.environ['POSTGRES_HOST']
        if 'POSTGRES_PORT' in os.environ:
            config.setdefault('database', {})['port'] = int(os.environ['POSTGRES_PORT'])
        if 'POSTGRES_DB' in os.environ:
            config.setdefault('database', {})['name'] = os.environ['POSTGRES_DB']
        if 'POSTGRES_USER' in os.environ:
            config.setdefault('database', {})['username'] = os.environ['POSTGRES_USER']
        if 'POSTGRES_PASSWORD' in os.environ:
            config.setdefault('database', {})['password'] = os.environ['POSTGRES_PASSWORD']
        
        # Broker API configuration
        if 'BROKER_API_KEY' in os.environ:
            config.setdefault('broker', {})['api_key'] = os.environ['BROKER_API_KEY']
        if 'BROKER_API_SECRET' in os.environ:
            config.setdefault('broker', {})['api_secret'] = os.environ['BROKER_API_SECRET']
        if 'BROKER_ACCESS_TOKEN' in os.environ:
            config.setdefault('broker', {})['access_token'] = os.environ['BROKER_ACCESS_TOKEN']
        
        # Logging level
        if 'LOG_LEVEL' in os.environ:
            config.setdefault('logging', {})['level'] = os.environ['LOG_LEVEL']
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Configuration section as dictionary
        """
        return self.config.get(section, {})
    
    def validate_required_keys(self, required_keys: list) -> None:
        """
        Validate that required configuration keys exist.
        
        Args:
            required_keys: List of required keys in dot notation
            
        Raises:
            ValueError: If any required key is missing
        """
        missing_keys = []
        
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    def __str__(self) -> str:
        """String representation (without sensitive data)."""
        safe_config = self._mask_sensitive_data(self.config.copy())
        return f"ConfigManager(config={safe_config})"
    
    def _mask_sensitive_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive configuration data for logging."""
        sensitive_keys = ['password', 'api_key', 'api_secret', 'access_token', 'token']
        
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = self._mask_sensitive_data(value)
            elif any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                if value:
                    config[key] = "*" * len(str(value))
        
        return config 
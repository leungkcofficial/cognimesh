# settings/plugin.py

from abc import ABC, abstractmethod
from typing import Any, Dict

class PluginInterface(ABC):
    """
    Abstract base class defining the interface for plugins.
    """

    def __init__(self):
        self.enabled = False  # By default, a plugin is not enabled

    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> None:
        """
        Setup the plugin with the given configuration. This method should handle
        reading configuration from the .env file and preparing the plugin to be used.
        """
        pass

    @abstractmethod
    def switch(self, enable: bool) -> None:
        """
        Control the enabled state of the plugin. If enable is True, the plugin is
        turned on; if False, the plugin is turned off.
        """
        pass

    @abstractmethod
    def delete(self) -> None:
        """
        Disable the plugin and clean up any resources it created, such as database
        tables, webpages, or frontend components.
        """
        pass

    def is_enabled(self) -> bool:
        """
        Check if the plugin is currently enabled.
        """
        return self.enabled

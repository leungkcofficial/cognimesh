from abc import ABC, abstractmethod

class PluginInterface(ABC):
    @abstractmethod
    def setup_database(self, db_connection):
        """
        Setup the database for the plugin, including creating tables if necessary.
        """
        pass
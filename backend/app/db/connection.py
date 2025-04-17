import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine import connection
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self):
        cloud_config = {
            'secure_connect_bundle': os.getenv('ASTRA_SECURE_CONNECT_BUNDLE')
        }

        auth_provider = PlainTextAuthProvider(
            os.getenv('ASTRA_CLIENT_ID'),
            os.getenv('ASTRA_CLIENT_SECRET')
        )

        self.cluster = Cluster(
            cloud=cloud_config,
            auth_provider=auth_provider
        )
        self.session = self.cluster.connect()
        
        # Set up the keyspace
        self.keyspace = os.getenv('ASTRA_KEYSPACE')
        self.session.set_keyspace(self.keyspace)
        
        # Set up connection for Object Mapper
        connection.setup(
            self.cluster,
            self.keyspace,
            protocol_version=4
        )

    def get_session(self):
        return self.session

    def close(self):
        self.cluster.shutdown()

db = DatabaseConnection()
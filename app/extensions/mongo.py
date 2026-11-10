import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class MongoExtension:
    """
    Extensión para encapsular la conexión a MongoDB utilizando PyMongo.
    Mantiene un cliente único reutilizable y gestiona índices y esquemas.
    """
    def __init__(self, app=None):
        self.client = None
        self.db = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        uri = app.config.get("MONGO_URI", "mongodb://localhost:27017")
        db_name = app.config.get("MONGO_DATABASE", "ia_assistant")
        is_testing = app.config.get("TESTING", False)

        if is_testing:
            try:
                import mongomock
                self.client = mongomock.MongoClient()
                self.db = self.client[db_name]
                logger.info("Usando mongomock para entorno de pruebas.")
            except ImportError:
                self.client = MongoClient(uri)
                self.db = self.client[db_name]
        else:
            try:
                # Intentar conectar con timeout rápido
                real_client = MongoClient(uri, serverSelectionTimeoutMS=2000)
                # Verificar conexión
                real_client.admin.command("ping")
                self.client = real_client
                self.db = self.client[db_name]
                logger.info(f"Conectado exitosamente a MongoDB en {uri}, base de datos: {db_name}")
            except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as err:
                logger.warning(
                    f"No se pudo conectar a MongoDB en {uri} ({err}). "
                    "Activando fallback en memoria (mongomock) para garantizar funcionamiento continuo."
                )
                import mongomock
                self.client = mongomock.MongoClient()
                self.db = self.client[db_name]

        self.init_indices()

    def get_db(self):
        return self.db

    def init_indices(self):
        """Crear índices obligatorios en las colecciones de MongoDB."""
        if self.db is None:
            return
        try:
            # Índices de Usuarios
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.users.create_index([("username", ASCENDING)], unique=True)

            # Índices de Chats
            self.db.chats.create_index([("user_id", ASCENDING)])
            self.db.chats.create_index([("updated_at", DESCENDING)])

            # Índices de Personalidades
            self.db.personalities.create_index([("owner_id", ASCENDING)])
            self.db.personalities.create_index([("visibility", ASCENDING)])
            self.db.personalities.create_index([("category", ASCENDING)])
            self.db.personalities.create_index([("created_at", DESCENDING)])
            self.db.personalities.create_index([("likes_count", DESCENDING)])
            self.db.personalities.create_index([("uses_count", DESCENDING)])

            # Índices de Interacciones (Likes) - Compuesto único
            self.db.interactions.create_index(
                [("user_id", ASCENDING), ("personality_id", ASCENDING), ("type", ASCENDING)],
                unique=True
            )

            # Índices de Amistades
            self.db.friendships.create_index([("requester_id", ASCENDING), ("receiver_id", ASCENDING)], unique=True)
            self.db.friendships.create_index([("status", ASCENDING)])

            logger.info("Índices de MongoDB inicializados correctamente.")
        except Exception as e:
            logger.warning(f"Aviso al crear índices de MongoDB: {e}")


mongo = MongoExtension()

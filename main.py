import os
import paramiko
import socketserver
import sqlalchemy as db
from paramiko.server import ServerInterface
from sqlalchemy import text
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED
import socket
import redis  # Добавлен импорт для работы с Redis
from sqlalchemy.exc import SQLAlchemyError

# Настройки SSH-сервера
SSH_HOST = "0.0.0.0"
SSH_PORT = 2222
SSH_KEY_FILE = "ssh_key"

# Настройки БД
DB_URL = "postgresql://root:root@localhost:5432/entities"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # Имя сервиса в Docker
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", 0))


class DBSSHServer(ServerInterface):
    def __init__(self):
        self.engine = db.create_engine(DB_URL)
        self.redis_client = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=False  # Для работы с бинарными данными файлов
        )
        super().__init__()

    def check_auth_password(self, username, password):
        return AUTH_SUCCESSFUL if (username == "admin" and password == "12345") else paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return OPEN_SUCCEEDED

    def check_channel_shell_request(self, channel):
        return True

    def execute_db_query(self, query):
        """Выполняет SQL-запрос и возвращает результат"""
        with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            try:
                conn.execute(text(query))
            except SQLAlchemyError as e:
                print(f"Ошибка: {e}")

    def load_file_to_redis(self, file_path, path_key, db_name):
        """Загружает файл в Redis"""
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()

            # Используем db_name как номер базы Redis (если нужно)
            # В реальном проекте лучше использовать разные ключи для разных БД
            self.redis_client.set(f"{db_name}:{path_key}", file_data)
            return f"File {file_path} loaded successfully with key {path_key}"
        except Exception as e:
            return f"Error loading file: {str(e)}"

    def download_file_from_redis(self, path_key, db_name, save_path=None):
        """Скачивает файл из Redis"""
        try:
            file_data = self.redis_client.get(f"{db_name}:{path_key}")
            if not file_data:
                return f"File with key {path_key} not found"

            if save_path is None:
                save_path = path_key  # Если путь не указан, сохраняем с именем ключа

            with open(save_path, 'wb') as file:
                file.write(file_data)
            return f"File saved to {save_path}"
        except Exception as e:
            return f"Error downloading file: {str(e)}"


class SSHHandler(socketserver.BaseRequestHandler):
    def handle(self):
        transport = None
        try:
            transport = paramiko.Transport(self.request)
            transport.add_server_key(paramiko.RSAKey(filename=SSH_KEY_FILE))

            ssh_server = DBSSHServer()
            transport.start_server(server=ssh_server)

            channel = transport.accept(20)
            if not channel:
                print("Client channel timeout")
                return

            channel.send("Welcome! Commands:\r\n"
                         "  'db: SQL_QUERY' - execute SQL query\r\n"
                         "  'load <file_path> <path_key> <db_name>' - upload file to Redis\r\n"
                         "  'download <path_key> <db_name>' - download file from Redis\r\n"
                         "  'exit' - disconnect\r\n\r\n")

            while True:
                try:
                    channel.send("db> ")
                    command = channel.recv(1024).decode().strip()
                    if not command or command.lower() == "exit":
                        break

                    if command.startswith("db:"):
                        result = ssh_server.execute_db_query(command[3:].strip())
                        channel.send(f"{result}\r\n")
                    elif command.startswith("load "):
                        parts = command.split()
                        if len(parts) != 4:
                            channel.send("Usage: load <file_path> <path_key> <db_name>\r\n")
                        else:
                            _, file_path, path_key, db_name = parts
                            result = ssh_server.load_file_to_redis(file_path, path_key, db_name)
                            channel.send(f"{result}\r\n")
                    elif command.startswith("download "):
                        parts = command.split()
                        if len(parts) != 3:
                            channel.send("Usage: download <path_key> <db_name>\r\n")
                        else:
                            _, path_key, db_name = parts
                            result = ssh_server.download_file_from_redis(path_key, db_name)
                            channel.send(f"{result}\r\n")
                    else:
                        channel.send("Unknown command. Available commands:\r\n"
                                     "  'db: SQL_QUERY'\r\n"
                                     "  'load <file_path> <path_key> <db_name>'\r\n"
                                     "  'download <path_key> <db_name>'\r\n"
                                     "  'exit'\r\n")

                except (socket.error, paramiko.SSHException) as e:
                    print(f"Client error: {e}")
                    break

        except Exception as e:
            print(f"Server crash: {e}")
        finally:
            if transport:
                transport.close()


# Генерация ключа сервера при первом запуске
if not os.path.exists(SSH_KEY_FILE):
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(SSH_KEY_FILE)

# Запуск сервера
try:
    server = socketserver.ThreadingTCPServer((SSH_HOST, SSH_PORT), SSHHandler)
    print(f"SSH DB Server started on {SSH_HOST}:{SSH_PORT}")
    server.serve_forever()
except KeyboardInterrupt:
    print("Server stopped.")

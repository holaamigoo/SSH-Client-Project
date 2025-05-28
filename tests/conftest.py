# Фикстура для создания временного SSH ключа для тестов
import pytest
import paramiko
import os
import redis
from sqlalchemy import create_engine
from unittest.mock import MagicMock, patch


@pytest.fixture
def ssh_key_file(tmp_path):
    key_file = tmp_path / "test_ssh_key"
    if not os.path.exists(key_file):
        key = paramiko.RSAKey.generate(2048)  # Генерация RSA ключа
        key.write_private_key_file(str(key_file))  # Сохранение в файл
    return str(key_file)  # Возвращает путь к файлу ключа

# Фикстура для мокирования Redis клиента
@pytest.fixture
def mock_redis():
    with patch('redis.StrictRedis') as mock:
        mock_redis = MagicMock()  # Создание mock-объекта Redis
        mock.return_value = mock_redis
        yield mock_redis  # Возвращает mock для использования в тестах

# Фикстура для мокирования SQLAlchemy engine
@pytest.fixture
def mock_db_engine():
    with patch('sqlalchemy.create_engine') as mock:
        mock_engine = MagicMock()  # Создание mock-объекта DB engine
        mock.return_value = mock_engine
        yield mock_engine

# Основная фикстура для тестирования DBSSHServer
@pytest.fixture
def db_ssh_server(ssh_key_file, mock_redis, mock_db_engine):
    from main import DBSSHServer
    return DBSSHServer()  # Возвращает инстанс сервера с mock-зависимостями

# Фикстура для мокирования SSH транспорта
@pytest.fixture
def mock_transport():
    transport = MagicMock()
    transport.is_active.return_value = True  # Имитация активного соединения
    return transport

# Фикстура для мокирования SSH канала
@pytest.fixture
def mock_channel():
    channel = MagicMock()
    channel.recv.return_value = b"exit"  # Имитация команды выхода
    return channel
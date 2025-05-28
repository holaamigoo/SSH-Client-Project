import pytest
import paramiko
from unittest.mock import MagicMock, patch

# Тест инициализации SSH обработчика
def test_ssh_handler_initialization(ssh_key_file):
    from main import SSHHandler

    mock_request = MagicMock()  # Мокирование сетевого запроса
    handler = SSHHandler(mock_request, ("127.0.0.1", 2222), None)

    # Простая проверка что обработчик создан
    assert handler is not None


# Тест обработки SSH соединения
def test_ssh_handler_handle_method(db_ssh_server, mock_transport, mock_channel):
    from main import SSHHandler

    mock_request = MagicMock()
    handler = SSHHandler(mock_request, ("127.0.0.1", 2222), None)

    with patch('paramiko.Transport', return_value=mock_transport):
        mock_transport.accept.return_value = mock_channel
        mock_channel.recv.side_effect = [b"db: SELECT 1", b"exit"]

        handler.handle()  # Вызов основного метода обработки

        # Проверка что методы транспорта были вызваны
        mock_transport.add_server_key.assert_called_once()
        mock_transport.start_server.assert_called_once()
        # Проверка что отправлено приветственное сообщение
        mock_channel.send.assert_any_call("Welcome! Commands:\r\n")


# Тест обработки различных команд
def test_command_processing(db_ssh_server, mock_channel):
    from main import SSHHandler

    mock_request = MagicMock()
    handler = SSHHandler(mock_request, ("127.0.0.1", 2222), None)
    handler.transport = MagicMock()
    handler.server = db_ssh_server

    # Тест обработки SQL команды
    with patch.object(db_ssh_server, 'execute_db_query') as mock_execute:
        handler.process_command("db: SELECT 1", mock_channel)
        mock_execute.assert_called_once_with("SELECT 1")

    # Тест обработки команды загрузки файла
    with patch.object(db_ssh_server, 'load_file_to_redis') as mock_load:
        handler.process_command("load tests.txt key db", mock_channel)
        mock_load.assert_called_once_with("tests.txt", "key", "db")

    # Тест обработки команды скачивания файла
    with patch.object(db_ssh_server, 'download_file_from_redis') as mock_download:
        handler.process_command("download key db", mock_channel)
        mock_download.assert_called_once_with("key", "db", None)

    # Тест обработки неизвестной команды
    mock_channel.reset_mock()
    handler.process_command("invalid command", mock_channel)
    # Проверка что отправлено сообщение о неизвестной команде
    mock_channel.send.assert_called_with("Unknown command. Available commands:\r\n"
                                         "  'db: SQL_QUERY'\r\n"
                                         "  'load <file_path> <path_key> <db_name>'\r\n"
                                         "  'download <path_key> <db_name>'\r\n"
                                         "  'exit'\r\n")
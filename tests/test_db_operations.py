from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError


# Тест успешного выполнения SQL запроса
def test_execute_db_query_success(db_ssh_server, mock_db_engine):
    mock_conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__.return_value = mock_conn

    query = "SELECT * FROM test_table"
    db_ssh_server.execute_db_query(query)  # Вызов тестируемого метода

    # Проверка что execute был вызван
    mock_conn.execute.assert_called_once()


# Тест обработки ошибки при выполнении SQL запроса
def test_execute_db_query_error(db_ssh_server, mock_db_engine, capsys):
    mock_conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.execute.side_effect = SQLAlchemyError("Test error")

    query = "INVALID SQL QUERY"
    db_ssh_server.execute_db_query(query)

    # Проверка вывода ошибки в stdout
    captured = capsys.readouterr()
    assert "Ошибка: Test error" in captured.out
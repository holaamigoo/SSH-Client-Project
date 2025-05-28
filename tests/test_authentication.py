from unittest.mock import MagicMock

import pytest
import paramiko
from paramiko.common import AUTH_SUCCESSFUL, AUTH_FAILED

# Тест успешной аутентификации с правильными credentials
def test_successful_authentication(db_ssh_server):
    assert db_ssh_server.check_auth_password("admin", "12345") == AUTH_SUCCESSFUL

# Тест неудачной аутентификации с неправильным именем пользователя
def test_failed_authentication_wrong_username(db_ssh_server):
    assert db_ssh_server.check_auth_password("wronguser", "12345") == AUTH_FAILED

# Тест неудачной аутентификации с неправильным паролем
def test_failed_authentication_wrong_password(db_ssh_server):
    assert db_ssh_server.check_auth_password("admin", "wrongpass") == AUTH_FAILED

# Тест успешного открытия SSH канала
def test_channel_request_success(db_ssh_server):
    assert db_ssh_server.check_channel_request("session", 1) == paramiko.OPEN_SUCCEEDED

# Тест успешного запроса shell на канале
def test_channel_shell_request_success(db_ssh_server):
    assert db_ssh_server.check_channel_shell_request(MagicMock()) is True
import pytest
import os

# Фикстура для создания временного тестового файла
@pytest.fixture
def test_file(tmp_path):
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("tests content")  # Создание файла с тестовым содержимым
    return str(file_path)


# Тест успешной загрузки файла в Redis
def test_load_file_to_redis_success(db_ssh_server, mock_redis, test_file):
    result = db_ssh_server.load_file_to_redis(test_file, "test_key", "test_db")

    # Проверка что set был вызван и возвращено сообщение об успехе
    mock_redis.set.assert_called_once()
    assert "loaded successfully" in result


# Тест ошибки при загрузке файла в Redis
def test_load_file_to_redis_error(db_ssh_server, mock_redis):
    mock_redis.set.side_effect = Exception("Redis error")

    result = db_ssh_server.load_file_to_redis("nonexistent.txt", "test_key", "test_db")

    # Проверка сообщения об ошибке
    assert "Error loading file" in result


# Тест успешного скачивания файла из Redis
def test_download_file_from_redis_success(db_ssh_server, mock_redis, tmp_path):
    mock_redis.get.return_value = b"tests content"  # Мокирование данных в Redis
    save_path = str(tmp_path / "downloaded.txt")

    result = db_ssh_server.download_file_from_redis("test_key", "test_db", save_path)

    # Проверка что файл сохранился с правильным содержимым
    assert "saved to" in result
    assert os.path.exists(save_path)
    with open(save_path, 'rb') as f:
        assert f.read() == b"tests content"


# Тест случая когда файл не найден в Redis
def test_download_file_from_redis_not_found(db_ssh_server, mock_redis):
    mock_redis.get.return_value = None  # Имитация отсутствия данных

    result = db_ssh_server.download_file_from_redis("nonexistent", "test_db")

    # Проверка сообщения о том что файл не найден
    assert "not found" in result


# Тест ошибки при скачивании файла из Redis
def test_download_file_from_redis_error(db_ssh_server, mock_redis):
    mock_redis.get.side_effect = Exception("Redis error")

    result = db_ssh_server.download_file_from_redis("test_key", "test_db")

    # Проверка сообщения об ошибке
    assert "Error downloading file" in result
import requests
import os


def get_last_modified(url):
    try:
        response = requests.head(url)
        response.raise_for_status()  # Перевірка на помилки HTTP
        last_modified = response.headers.get('Last-Modified')
        return last_modified
    except requests.exceptions.RequestException as e:
        print(f"Помилка при отриманні заголовка Last-Modified: {e}")
        return None


# Використання функції
url = 'https://api.safecast.org/system/measurements.tar.gz?_gl=1*15e18sa*_ga*NTI4NDE2MDM0LjE3MzUzODI4MTQ.*_ga_GSRZYX6XXY*MTczOTM2OTUwMS4xMS4wLjE3MzkzNjk1MDEuMC4wLjA.'
last_modified = get_last_modified(url)
if last_modified:
    print(f"Файл був оновлений останній раз: {last_modified}")
else:
    print("Не вдалося отримати інформацію про оновлення файлу.")


def is_new_file_available(file_url, size_file_path):
    try:
        response = requests.head(file_url)
        response.raise_for_status()
        remote_file_size = int(response.headers.get('content-length', 0))

        if os.path.exists(size_file_path):
            with open(size_file_path, 'r') as f:
                previous_file_size = int(f.read().strip())
        else:
            previous_file_size = 0

        return remote_file_size != previous_file_size
    except requests.RequestException as e:
        print(f"Error checking file: {e}")
        return False


def save_file_size(size_file_path, file_size):
    try:
        with open(size_file_path, 'w') as f:
            f.write(str(file_size))
        print(f"File size saved successfully: {file_size}")
    except IOError as e:
        print(f"Error saving file size: {e}")


def download_file(file_url, local_file_path, size_file_path):
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        with open(local_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        save_file_size(
            size_file_path, response.headers.get('content-length', 0))
        print(f"File downloaded successfully: {local_file_path}")
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")


def main(file_url, local_file_path, size_file_path):
    if is_new_file_available(file_url, size_file_path):
        print("A new file is available. Downloading...")
        download_file(file_url, local_file_path, size_file_path)
    else:
        print("No new file available.")


if __name__ == "__main__":
    FILE_URL = "https://example.com/path/to/file"
    LOCAL_FILE_PATH = "path/to/local/file"
    SIZE_FILE_PATH = "path/to/local/file_size.txt"
    main(FILE_URL, LOCAL_FILE_PATH, SIZE_FILE_PATH)

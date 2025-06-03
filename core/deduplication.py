import hashlib
import os

def calculate_file_hash(file_path, chunk_size=4 * 1024 * 1024):
    """
    Calcula o hash SHA-256 de um arquivo.

    :param file_path: Caminho do arquivo
    :param chunk_size: Tamanho dos blocos para leitura (4MB padrão)
    :return: Hash SHA-256 em hexadecimal
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_data_hash(data: bytes) -> str:
    """
    Calcula o hash SHA-256 de um bloco de dados.

    :param data: Dados em bytes
    :return: Hash SHA-256 em hexadecimal
    """
    return hashlib.sha256(data).hexdigest()

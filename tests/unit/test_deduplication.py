#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitarios para o modulo de deduplicacao
"""

import unittest
import tempfile
import os
import hashlib
from pathlib import Path
import sys

# Adicionar o diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.deduplication import calculate_file_hash, calculate_data_hash

class TestDeduplication(unittest.TestCase):
    """Testes para funcionalidades de deduplicacao"""
    
    def setUp(self):
        """Configuracao inicial para cada teste"""
        self.test_data = b"Este e um arquivo de teste para deduplicacao"
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        
        # Criar arquivo de teste
        with open(self.test_file, 'wb') as f:
            f.write(self.test_data)
    
    def tearDown(self):
        """Limpeza apos cada teste"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def test_calculate_file_hash(self):
        """Testar calculo de hash de arquivo"""
        # Calcular hash esperado
        expected_hash = hashlib.sha256(self.test_data).hexdigest()
        
        # Calcular hash usando a funcao
        calculated_hash = calculate_file_hash(self.test_file)
        
        self.assertEqual(calculated_hash, expected_hash)
    
    def test_calculate_data_hash(self):
        """Testar calculo de hash de dados"""
        # Calcular hash esperado
        expected_hash = hashlib.sha256(self.test_data).hexdigest()
        
        # Calcular hash usando a funcao
        calculated_hash = calculate_data_hash(self.test_data)
        
        self.assertEqual(calculated_hash, expected_hash)
    
    def test_file_not_found(self):
        """Testar comportamento com arquivo inexistente"""
        non_existent_file = os.path.join(self.temp_dir, "non_existent.txt")
        
        with self.assertRaises(FileNotFoundError):
            calculate_file_hash(non_existent_file)
    
    def test_empty_file(self):
        """Testar hash de arquivo vazio"""
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        
        # Criar arquivo vazio
        with open(empty_file, 'wb') as f:
            pass
        
        # Hash de dados vazios
        expected_hash = hashlib.sha256(b"").hexdigest()
        calculated_hash = calculate_file_hash(empty_file)
        
        self.assertEqual(calculated_hash, expected_hash)
        
        # Limpar
        os.remove(empty_file)
    
    def test_large_file(self):
        """Testar hash de arquivo grande"""
        large_data = b"A" * (1024 * 1024)  # 1MB de dados
        large_file = os.path.join(self.temp_dir, "large.txt")
        
        # Criar arquivo grande
        with open(large_file, 'wb') as f:
            f.write(large_data)
        
        # Calcular hashes
        expected_hash = hashlib.sha256(large_data).hexdigest()
        calculated_hash = calculate_file_hash(large_file)
        
        self.assertEqual(calculated_hash, expected_hash)
        
        # Limpar
        os.remove(large_file)
    
    def test_duplicate_detection(self):
        """Testar deteccao de arquivos duplicados"""
        # Criar segundo arquivo com mesmo conteudo
        duplicate_file = os.path.join(self.temp_dir, "duplicate.txt")
        with open(duplicate_file, 'wb') as f:
            f.write(self.test_data)
        
        # Calcular hashes
        hash1 = calculate_file_hash(self.test_file)
        hash2 = calculate_file_hash(duplicate_file)
        
        # Devem ser iguais
        self.assertEqual(hash1, hash2)
        
        # Limpar
        os.remove(duplicate_file)
    
    def test_different_files(self):
        """Testar que arquivos diferentes têm hashes diferentes"""
        different_data = b"Este e um arquivo diferente"
        different_file = os.path.join(self.temp_dir, "different.txt")
        
        # Criar arquivo diferente
        with open(different_file, 'wb') as f:
            f.write(different_data)
        
        # Calcular hashes
        hash1 = calculate_file_hash(self.test_file)
        hash2 = calculate_file_hash(different_file)
        
        # Devem ser diferentes
        self.assertNotEqual(hash1, hash2)
        
        # Limpar
        os.remove(different_file)

if __name__ == '__main__':
    unittest.main()
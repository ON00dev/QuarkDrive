
# QuarkDrive 🚀

**Sistema de Armazenamento Otimizado com Deduplicação e Compressão**

QuarkDrive é uma solução avançada de armazenamento que combina deduplicação inteligente, compressão eficiente e cache híbrido para maximizar a eficiência do espaço em disco e melhorar a performance de acesso aos dados.

## ✨ Características Principais

- **🔄 Deduplicação Inteligente**: Elimina arquivos duplicados automaticamente
- **📦 Compressão Avançada**: Utiliza ZSTD para compressão de alta performance
- **⚡ Extensões C++**: Módulos otimizados para máxima velocidade
- **💾 Cache Híbrido**: Sistema de cache RAM + SSD para acesso rápido
- **🖥️ Interface Gráfica**: GUI intuitiva desenvolvida em PyQt5
- **📁 Sistema de Arquivos Virtual**: Montagem transparente via FUSE/Dokan
- **📊 Estatísticas Detalhadas**: Monitoramento em tempo real do desempenho

## 🛠️ Instalação

### Pré-requisitos

- Python 3.8+
- Windows 10+ ou Linux
- 4GB RAM (recomendado)
- 1GB espaço livre em disco

### Instalação Rápida

```bash
# Clonar o repositório
git clone https://github.com/ON00dev/QuarkDrive.git
cd QuarkDrive

# Instalar dependências
pip install -r requirements.txt

# Compilar extensões C++ (opcional, mas recomendado)
python compile_extensions.py

# Executar
python main.py gui
```

### Instalação via Executável
Baixe o executável pré-compilado da seção [**releases**](https://github.com/ON00dev/QuarkDrive/releases) e execute diretamente.
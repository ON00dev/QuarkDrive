#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <zstd.h>
#include <stdexcept>

namespace py = pybind11;

class FastCompressor {
private:
    int compression_level;
    ZSTD_CCtx* cctx;
    ZSTD_DCtx* dctx;
    
public:
    FastCompressor(int level = 5) : compression_level(level) {
        cctx = ZSTD_createCCtx();
        dctx = ZSTD_createDCtx();
        if (!cctx || !dctx) {
            throw std::runtime_error("Failed to create ZSTD contexts");
        }
    }
    
    ~FastCompressor() {
        if (cctx) ZSTD_freeCCtx(cctx);
        if (dctx) ZSTD_freeDCtx(dctx);
    }
    
    std::vector<uint8_t> compress(const std::vector<uint8_t>& data) {
        size_t max_compressed_size = ZSTD_compressBound(data.size());
        std::vector<uint8_t> compressed(max_compressed_size);
        
        size_t compressed_size = ZSTD_compressCCtx(
            cctx,
            compressed.data(), max_compressed_size,
            data.data(), data.size(),
            compression_level
        );
        
        if (ZSTD_isError(compressed_size)) {
            throw std::runtime_error("Compression failed: " + std::string(ZSTD_getErrorName(compressed_size)));
        }
        
        compressed.resize(compressed_size);
        return compressed;
    }
    
    std::vector<uint8_t> decompress(const std::vector<uint8_t>& compressed_data) {
        unsigned long long decompressed_size = ZSTD_getFrameContentSize(
            compressed_data.data(), compressed_data.size()
        );
        
        if (decompressed_size == ZSTD_CONTENTSIZE_ERROR) {
            throw std::runtime_error("Invalid compressed data");
        }
        
        if (decompressed_size == ZSTD_CONTENTSIZE_UNKNOWN) {
            // Fallback para tamanho desconhecido
            decompressed_size = compressed_data.size() * 4; // Estimativa
        }
        
        std::vector<uint8_t> decompressed(decompressed_size);
        
        size_t actual_size = ZSTD_decompressDCtx(
            dctx,
            decompressed.data(), decompressed_size,
            compressed_data.data(), compressed_data.size()
        );
        
        if (ZSTD_isError(actual_size)) {
            throw std::runtime_error("Decompression failed: " + std::string(ZSTD_getErrorName(actual_size)));
        }
        
        decompressed.resize(actual_size);
        return decompressed;
    }
    
    double get_compression_ratio(const std::vector<uint8_t>& original, const std::vector<uint8_t>& compressed) {
        if (original.empty()) return 0.0;
        return (1.0 - static_cast<double>(compressed.size()) / static_cast<double>(original.size())) * 100.0;
    }
    
    void set_compression_level(int level) {
        if (level < 1 || level > 22) {
            throw std::invalid_argument("Compression level must be between 1 and 22");
        }
        compression_level = level;
    }
    
    int get_compression_level() const {
        return compression_level;
    }
};

// Funções utilitárias para compressão rápida
std::vector<uint8_t> fast_compress(const std::vector<uint8_t>& data, int level = 5) {
    FastCompressor compressor(level);
    return compressor.compress(data);
}

std::vector<uint8_t> fast_decompress(const std::vector<uint8_t>& compressed_data) {
    FastCompressor compressor;
    return compressor.decompress(compressed_data);
}

double calculate_compression_ratio(const std::vector<uint8_t>& original, const std::vector<uint8_t>& compressed) {
    if (original.empty()) return 0.0;
    return (1.0 - static_cast<double>(compressed.size()) / static_cast<double>(original.size())) * 100.0;
}

PYBIND11_MODULE(compression_module, m) {
    m.doc() = "Fast compression module using ZSTD";
    
    py::class_<FastCompressor>(m, "FastCompressor")
        .def(py::init<int>(), py::arg("level") = 5)
        .def("compress", &FastCompressor::compress, "Compress data using ZSTD")
        .def("decompress", &FastCompressor::decompress, "Decompress ZSTD data")
        .def("get_compression_ratio", &FastCompressor::get_compression_ratio, "Calculate compression ratio")
        .def("set_compression_level", &FastCompressor::set_compression_level, "Set compression level (1-22)")
        .def("get_compression_level", &FastCompressor::get_compression_level, "Get current compression level");
    
    m.def("fast_compress", &fast_compress, "Quick compress function", py::arg("data"), py::arg("level") = 5);
    m.def("fast_decompress", &fast_decompress, "Quick decompress function");
    m.def("calculate_compression_ratio", &calculate_compression_ratio, "Calculate compression ratio between original and compressed data");
}
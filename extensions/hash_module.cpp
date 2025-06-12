#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <array>
#include <openssl/sha.h>
#include <openssl/md5.h>
#include <xxhash.h>
#include <iomanip>
#include <sstream>
#include <fstream>
#include <stdexcept>

namespace py = pybind11;

class FastHasher {
public:
    // SHA-256 hash
    static std::string sha256(const std::vector<uint8_t>& data) {
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256_CTX sha256;
        SHA256_Init(&sha256);
        SHA256_Update(&sha256, data.data(), data.size());
        SHA256_Final(hash, &sha256);
        
        return bytes_to_hex(hash, SHA256_DIGEST_LENGTH);
    }
    
    // SHA-256 hash de arquivo
    static std::string sha256_file(const std::string& filepath) {
        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file: " + filepath);
        }
        
        SHA256_CTX sha256;
        SHA256_Init(&sha256);
        
        char buffer[8192];
        while (file.read(buffer, sizeof(buffer)) || file.gcount() > 0) {
            SHA256_Update(&sha256, buffer, file.gcount());
        }
        
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256_Final(hash, &sha256);
        
        return bytes_to_hex(hash, SHA256_DIGEST_LENGTH);
    }
    
    // MD5 hash (para compatibilidade)
    static std::string md5(const std::vector<uint8_t>& data) {
        unsigned char hash[MD5_DIGEST_LENGTH];
        MD5_CTX md5;
        MD5_Init(&md5);
        MD5_Update(&md5, data.data(), data.size());
        MD5_Final(hash, &md5);
        
        return bytes_to_hex(hash, MD5_DIGEST_LENGTH);
    }
    
    // XXHash (muito rapido para deduplicacao)
    static uint64_t xxhash64(const std::vector<uint8_t>& data, uint64_t seed = 0) {
        return XXH64(data.data(), data.size(), seed);
    }
    
    static std::string xxhash64_hex(const std::vector<uint8_t>& data, uint64_t seed = 0) {
        uint64_t hash = XXH64(data.data(), data.size(), seed);
        std::stringstream ss;
        ss << std::hex << hash;
        return ss.str();
    }
    
    // XXHash de arquivo
    static uint64_t xxhash64_file(const std::string& filepath, uint64_t seed = 0) {
        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file: " + filepath);
        }
        
        XXH64_state_t* state = XXH64_createState();
        if (!state) {
            throw std::runtime_error("Failed to create XXHash state");
        }
        
        XXH64_reset(state, seed);
        
        char buffer[8192];
        while (file.read(buffer, sizeof(buffer)) || file.gcount() > 0) {
            XXH64_update(state, buffer, file.gcount());
        }
        
        uint64_t hash = XXH64_digest(state);
        XXH64_freeState(state);
        
        return hash;
    }
    
    // Hash incremental para streams grandes
    class IncrementalHasher {
    private:
        SHA256_CTX sha256_ctx;
        XXH64_state_t* xxh_state;
        bool sha256_initialized;
        bool xxh_initialized;
        
    public:
        IncrementalHasher() : sha256_initialized(false), xxh_initialized(false), xxh_state(nullptr) {}
        
        ~IncrementalHasher() {
            if (xxh_state) {
                XXH64_freeState(xxh_state);
            }
        }
        
        void init_sha256() {
            SHA256_Init(&sha256_ctx);
            sha256_initialized = true;
        }
        
        void init_xxhash(uint64_t seed = 0) {
            xxh_state = XXH64_createState();
            if (!xxh_state) {
                throw std::runtime_error("Failed to create XXHash state");
            }
            XXH64_reset(xxh_state, seed);
            xxh_initialized = true;
        }
        
        void update(const std::vector<uint8_t>& data) {
            if (sha256_initialized) {
                SHA256_Update(&sha256_ctx, data.data(), data.size());
            }
            if (xxh_initialized && xxh_state) {
                XXH64_update(xxh_state, data.data(), data.size());
            }
        }
        
        std::string finalize_sha256() {
            if (!sha256_initialized) {
                throw std::runtime_error("SHA256 not initialized");
            }
            unsigned char hash[SHA256_DIGEST_LENGTH];
            SHA256_Final(hash, &sha256_ctx);
            sha256_initialized = false;
            return bytes_to_hex(hash, SHA256_DIGEST_LENGTH);
        }
        
        uint64_t finalize_xxhash() {
            if (!xxh_initialized || !xxh_state) {
                throw std::runtime_error("XXHash not initialized");
            }
            uint64_t hash = XXH64_digest(xxh_state);
            XXH64_freeState(xxh_state);
            xxh_state = nullptr;
            xxh_initialized = false;
            return hash;
        }
    };
    
private:
    static std::string bytes_to_hex(const unsigned char* bytes, size_t length) {
        std::stringstream ss;
        ss << std::hex << std::setfill('0');
        for (size_t i = 0; i < length; ++i) {
            ss << std::setw(2) << static_cast<unsigned>(bytes[i]);
        }
        return ss.str();
    }
};

// Funcões utilitarias
std::string quick_sha256(const std::vector<uint8_t>& data) {
    return FastHasher::sha256(data);
}

std::string quick_sha256_file(const std::string& filepath) {
    return FastHasher::sha256_file(filepath);
}

uint64_t quick_xxhash(const std::vector<uint8_t>& data) {
    return FastHasher::xxhash64(data);
}

std::string quick_xxhash_hex(const std::vector<uint8_t>& data) {
    return FastHasher::xxhash64_hex(data);
}

uint64_t quick_xxhash_file(const std::string& filepath) {
    return FastHasher::xxhash64_file(filepath);
}

PYBIND11_MODULE(hash_module, m) {
    m.doc() = "Fast hashing module with SHA-256, MD5, and XXHash support";
    
    py::class_<FastHasher>(m, "FastHasher")
        .def_static("sha256", &FastHasher::sha256, "Calculate SHA-256 hash of data")
        .def_static("sha256_file", &FastHasher::sha256_file, "Calculate SHA-256 hash of file")
        .def_static("md5", &FastHasher::md5, "Calculate MD5 hash of data")
        .def_static("xxhash64", &FastHasher::xxhash64, "Calculate XXHash64 of data", py::arg("data"), py::arg("seed") = 0)
        .def_static("xxhash64_hex", &FastHasher::xxhash64_hex, "Calculate XXHash64 of data as hex string", py::arg("data"), py::arg("seed") = 0)
        .def_static("xxhash64_file", &FastHasher::xxhash64_file, "Calculate XXHash64 of file", py::arg("filepath"), py::arg("seed") = 0);
    
    py::class_<FastHasher::IncrementalHasher>(m, "IncrementalHasher")
        .def(py::init<>())
        .def("init_sha256", &FastHasher::IncrementalHasher::init_sha256, "Initialize SHA-256 hasher")
        .def("init_xxhash", &FastHasher::IncrementalHasher::init_xxhash, "Initialize XXHash hasher", py::arg("seed") = 0)
        .def("update", &FastHasher::IncrementalHasher::update, "Update hash with new data")
        .def("finalize_sha256", &FastHasher::IncrementalHasher::finalize_sha256, "Finalize and get SHA-256 hash")
        .def("finalize_xxhash", &FastHasher::IncrementalHasher::finalize_xxhash, "Finalize and get XXHash");
    
    // Funcões utilitarias
    m.def("quick_sha256", &quick_sha256, "Quick SHA-256 hash function");
    m.def("quick_sha256_file", &quick_sha256_file, "Quick SHA-256 file hash function");
    m.def("quick_xxhash", &quick_xxhash, "Quick XXHash function");
    m.def("quick_xxhash_hex", &quick_xxhash_hex, "Quick XXHash hex function");
    m.def("quick_xxhash_file", &quick_xxhash_file, "Quick XXHash file function");
}
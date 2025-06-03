#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <windows.h>
#include <winioctl.h>
#include <string>
#include <map>
#include <memory>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <atomic>
#include <functional>
#include <algorithm>  // Para std::min e std::max

namespace py = pybind11;

// Estrutura para requisições de I/O
struct IORequest {
    enum Type { READ, WRITE, LIST, EXISTS, SIZE };
    
    Type type;
    std::string path;
    std::vector<char> data;
    size_t offset;
    size_t size;
    HANDLE completion_event;
    DWORD result;
    std::vector<char> response_data;
    
    IORequest(Type t, const std::string& p) 
        : type(t), path(p), offset(0), size(0), result(0) {
        completion_event = CreateEvent(NULL, TRUE, FALSE, NULL);
    }
    
    ~IORequest() {
        if (completion_event != NULL) {
            CloseHandle(completion_event);
        }
    }
};

class WindowsVFS {
private:
    std::string mount_point;
    std::string backend_path;
    std::thread mount_thread;
    std::atomic<bool> is_mounted{false};
    std::atomic<bool> should_stop{false};
    
    // Thread safety
    std::mutex callbacks_mutex;
    std::mutex io_queue_mutex;
    std::condition_variable io_queue_cv;
    std::queue<std::shared_ptr<IORequest>> io_queue;
    
    // Callbacks thread-safe
    std::function<py::bytes(const std::string&)> read_callback;
    std::function<void(const std::string&, const py::bytes&)> write_callback;
    std::function<std::vector<std::string>(const std::string&)> list_callback;
    std::function<bool(const std::string&)> exists_callback;
    std::function<size_t(const std::string&)> size_callback;
    
    // Pool de threads para callbacks Python
    std::vector<std::thread> callback_threads;
    static const size_t CALLBACK_THREAD_COUNT = 4;
    
public:
    WindowsVFS(const std::string& backend) : backend_path(backend) {}
    
    ~WindowsVFS() {
        if (is_mounted.load()) {
            unmount();
        }
    }
    
    // Thread-safe callback setters
    void set_read_callback(std::function<py::bytes(const std::string&)> cb) {
        std::lock_guard<std::mutex> lock(callbacks_mutex);
        read_callback = cb;
    }
    
    void set_write_callback(std::function<void(const std::string&, const py::bytes&)> cb) {
        std::lock_guard<std::mutex> lock(callbacks_mutex);
        write_callback = cb;
    }
    
    void set_list_callback(std::function<std::vector<std::string>(const std::string&)> cb) {
        std::lock_guard<std::mutex> lock(callbacks_mutex);
        list_callback = cb;
    }
    
    void set_exists_callback(std::function<bool(const std::string&)> cb) {
        std::lock_guard<std::mutex> lock(callbacks_mutex);
        exists_callback = cb;
    }
    
    void set_size_callback(std::function<size_t(const std::string&)> cb) {
        std::lock_guard<std::mutex> lock(callbacks_mutex);
        size_callback = cb;
    }
    
    bool mount(const std::string& drive_letter) {
        if (is_mounted.load()) {
            return false;
        }
        
        mount_point = drive_letter;
        should_stop.store(false);
        
        // Iniciar threads de callback
        start_callback_threads();
        
        // Iniciar thread principal de montagem
        mount_thread = std::thread([this]() {
            this->mount_worker();
        });
        
        is_mounted.store(true);
        return true;
    }
    
    bool unmount() {
        if (!is_mounted.load()) {
            return false;
        }
        
        should_stop.store(true);
        is_mounted.store(false);
        
        // Notificar todas as threads
        io_queue_cv.notify_all();
        
        // Aguardar threads de callback terminarem
        stop_callback_threads();
        
        // Aguardar thread principal terminar
        if (mount_thread.joinable()) {
            mount_thread.join();
        }
        
        return true;
    }
    
    bool is_active() const {
        return is_mounted.load();
    }
    
    std::string get_mount_point() const {
        return mount_point;
    }
    
private:
    void start_callback_threads() {
        for (size_t i = 0; i < CALLBACK_THREAD_COUNT; ++i) {
            callback_threads.emplace_back([this]() {
                this->callback_worker();
            });
        }
    }
    
    void stop_callback_threads() {
        for (auto& thread : callback_threads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        callback_threads.clear();
    }
    
    void callback_worker() {
        while (!should_stop.load()) {
            std::shared_ptr<IORequest> request;
            
            // Aguardar por requisições
            {
                std::unique_lock<std::mutex> lock(io_queue_mutex);
                io_queue_cv.wait(lock, [this] { 
                    return !io_queue.empty() || should_stop.load(); 
                });
                
                if (should_stop.load()) break;
                
                if (!io_queue.empty()) {
                    request = io_queue.front();
                    io_queue.pop();
                }
            }
            
            if (request) {
                process_io_request(request);
            }
        }
    }
    
    void process_io_request(std::shared_ptr<IORequest> request) {
        try {
            std::lock_guard<std::mutex> lock(callbacks_mutex);
            
            switch (request->type) {
                case IORequest::READ:
                    if (read_callback) {
                        // Liberar GIL antes de chamar callback Python
                        py::bytes data;
                        {
                            py::gil_scoped_acquire acquire;
                            data = read_callback(request->path);
                        }
                        
                        std::string str_data = data;
                        size_t bytes_to_copy = std::min(request->size, 
                                                       str_data.length() - request->offset);
                        
                        if (bytes_to_copy > 0) {
                            request->response_data.resize(bytes_to_copy);
                            std::memcpy(request->response_data.data(), 
                                      str_data.data() + request->offset, 
                                      bytes_to_copy);
                        }
                        request->result = static_cast<DWORD>(bytes_to_copy);
                    }
                    break;
                    
                case IORequest::WRITE:
                    if (write_callback) {
                        py::gil_scoped_acquire acquire;
                        py::bytes data(request->data.data(), request->data.size());
                        write_callback(request->path, data);
                        request->result = static_cast<DWORD>(request->data.size());
                    }
                    break;
                    
                case IORequest::LIST:
                    if (list_callback) {
                        py::gil_scoped_acquire acquire;
                        auto files = list_callback(request->path);
                        // Serializar lista de arquivos
                        std::string result;
                        for (const auto& file : files) {
                            result += file + "\n";
                        }
                        request->response_data.assign(result.begin(), result.end());
                        request->result = static_cast<DWORD>(result.length());
                    }
                    break;
                    
                case IORequest::EXISTS:
                    if (exists_callback) {
                        py::gil_scoped_acquire acquire;
                        bool exists = exists_callback(request->path);
                        request->result = exists ? 1 : 0;
                    }
                    break;
                    
                case IORequest::SIZE:
                    if (size_callback) {
                        py::gil_scoped_acquire acquire;
                        size_t size = size_callback(request->path);
                        request->result = static_cast<DWORD>(size);
                    }
                    break;
            }
        } catch (const std::exception& e) {
            // Log erro e definir resultado como erro
            request->result = ERROR_INVALID_FUNCTION;
        }
        
        // Sinalizar conclusão
        SetEvent(request->completion_event);
    }
    
    void mount_worker() {
        // Implementação mais robusta usando Windows API
        
        // 1. Criar dispositivo virtual
        std::string device_name = "\\\\.\\" + mount_point.substr(0, 1) + ":";
        
        // 2. Registrar como driver de sistema de arquivos
        HANDLE device_handle = CreateFile(
            device_name.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            NULL,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            NULL
        );
        
        if (device_handle == INVALID_HANDLE_VALUE) {
            // Fallback: usar subst para criar unidade virtual
            std::string subst_cmd = "subst " + mount_point + " \"" + backend_path + "\"";
            system(subst_cmd.c_str());
        }
        
        // 3. Loop principal para processar requisições
        while (!should_stop.load()) {
            // Implementar comunicação com driver via DeviceIoControl
            // Por enquanto, usar polling com intervalo menor
            
            // Verificar se há requisições pendentes do sistema
            check_pending_requests();
            
            // Sleep menor para melhor responsividade
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        
        // Cleanup
        if (device_handle != INVALID_HANDLE_VALUE) {
            CloseHandle(device_handle);
        } else {
            // Remover subst
            std::string subst_cmd = "subst " + mount_point + " /d";
            system(subst_cmd.c_str());
        }
    }
    
    void check_pending_requests() {
        // Implementar verificação de requisições do sistema de arquivos
        // Esta é uma implementação simplificada
        
        // Em uma implementação real, você usaria:
        // - DeviceIoControl para comunicar com driver
        // - Overlapped I/O para operações assíncronas
        // - Completion ports para alta performance
        
        // Por enquanto, simular algumas operações básicas
        static int counter = 0;
        if (++counter % 1000 == 0) {
            // Simular requisição de listagem periódica
            auto request = std::make_shared<IORequest>(IORequest::LIST, "/");
            
            {
                std::lock_guard<std::mutex> lock(io_queue_mutex);
                io_queue.push(request);
            }
            io_queue_cv.notify_one();
        }
    }
    
    // API pública para operações síncronas (para testes)
public:
    DWORD sync_read(const std::string& path, char* buffer, DWORD size, DWORD offset) {
        auto request = std::make_shared<IORequest>(IORequest::READ, path);
        request->size = size;
        request->offset = offset;
        
        // Adicionar à fila
        {
            std::lock_guard<std::mutex> lock(io_queue_mutex);
            io_queue.push(request);
        }
        io_queue_cv.notify_one();
        
        // Aguardar conclusão
        WaitForSingleObject(request->completion_event, INFINITE);
        
        // Copiar dados
        if (request->result > 0 && buffer) {
            std::memcpy(buffer, request->response_data.data(), request->result);
        }
        
        return request->result;
    }
    
    DWORD sync_write(const std::string& path, const char* buffer, DWORD size) {
        auto request = std::make_shared<IORequest>(IORequest::WRITE, path); // Corrigido para WRITE
        request->data.assign(buffer, buffer + size);
        
        {
            std::lock_guard<std::mutex> lock(io_queue_mutex);
            io_queue.push(request);
        }
        io_queue_cv.notify_one();
        
        WaitForSingleObject(request->completion_event, INFINITE);
        return request->result;
    }
};

// Classe para gerenciar múltiplas montagens
class WindowsVFSManager {
private:
    std::map<std::string, std::unique_ptr<WindowsVFS>> mounted_drives;
    
public:
    bool mount_drive(const std::string& drive_letter, const std::string& backend_path) {
        if (mounted_drives.find(drive_letter) != mounted_drives.end()) {
            return false; // Já montado
        }
        
        auto vfs = std::make_unique<WindowsVFS>(backend_path);
        if (vfs->mount(drive_letter)) {
            mounted_drives[drive_letter] = std::move(vfs);
            return true;
        }
        
        return false;
    }
    
    bool unmount_drive(const std::string& drive_letter) {
        auto it = mounted_drives.find(drive_letter);
        if (it != mounted_drives.end()) {
            it->second->unmount();
            mounted_drives.erase(it);
            return true;
        }
        return false;
    }
    
    std::vector<std::string> get_mounted_drives() {
        std::vector<std::string> drives;
        for (const auto& pair : mounted_drives) {
            drives.push_back(pair.first);
        }
        return drives;
    }
    
    WindowsVFS* get_vfs(const std::string& drive_letter) {
        auto it = mounted_drives.find(drive_letter);
        return (it != mounted_drives.end()) ? it->second.get() : nullptr;
    }
};

// Instância global do gerenciador
static WindowsVFSManager vfs_manager;

// Funções Python-callable
bool mount_windows_drive(const std::string& drive_letter, const std::string& backend_path) {
    return vfs_manager.mount_drive(drive_letter, backend_path);
}

bool unmount_windows_drive(const std::string& drive_letter) {
    return vfs_manager.unmount_drive(drive_letter);
}

std::vector<std::string> get_mounted_windows_drives() {
    return vfs_manager.get_mounted_drives();
}

void set_drive_callbacks(const std::string& drive_letter,
                        std::function<py::bytes(const std::string&)> read_cb,
                        std::function<void(const std::string&, const py::bytes&)> write_cb,
                        std::function<std::vector<std::string>(const std::string&)> list_cb,
                        std::function<bool(const std::string&)> exists_cb,
                        std::function<size_t(const std::string&)> size_cb) {
    WindowsVFS* vfs = vfs_manager.get_vfs(drive_letter);
    if (vfs) {
        vfs->set_read_callback(read_cb);
        vfs->set_write_callback(write_cb);
        vfs->set_list_callback(list_cb);
        vfs->set_exists_callback(exists_cb);
        vfs->set_size_callback(size_cb);
    }
}

// Binding do pybind11 com melhorias
PYBIND11_MODULE(windows_vfs_module, m) {
    m.doc() = "Thread-safe Windows Virtual File System Module for QuarkDrive";
    
    // Configurar release do GIL para callbacks
    py::options options;
    options.disable_function_signatures();
    
    m.def("mount_drive", &mount_windows_drive, 
          "Mount a virtual drive", py::call_guard<py::gil_scoped_release>());
    m.def("unmount_drive", &unmount_windows_drive, 
          "Unmount a virtual drive", py::call_guard<py::gil_scoped_release>());
    m.def("get_mounted_drives", &get_mounted_windows_drives, 
          "Get list of mounted drives");
    m.def("set_callbacks", &set_drive_callbacks, 
          "Set filesystem operation callbacks");
    
    py::class_<WindowsVFS>(m, "WindowsVFS")
        .def(py::init<const std::string&>())
        .def("mount", &WindowsVFS::mount, py::call_guard<py::gil_scoped_release>())
        .def("unmount", &WindowsVFS::unmount, py::call_guard<py::gil_scoped_release>())
        .def("is_active", &WindowsVFS::is_active)
        .def("get_mount_point", &WindowsVFS::get_mount_point)
        .def("sync_read", &WindowsVFS::sync_read, py::call_guard<py::gil_scoped_release>())
        .def("sync_write", &WindowsVFS::sync_write, py::call_guard<py::gil_scoped_release>());
}
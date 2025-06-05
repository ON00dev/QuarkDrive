#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <dokan/dokan.h>
#include <dokan/fileinfo.h>
#include <windows.h>
#include <string>
#include <map>
#include <memory>
#include <mutex>
#include <thread>

namespace py = pybind11;

class DokanyVFS {
private:
    std::wstring mount_point;
    DOKAN_HANDLE dokan_handle;
    bool is_mounted;
    
    // Callbacks Python thread-safe
    std::mutex callbacks_mutex;
    std::function<py::bytes(const std::string&)> read_callback;
    std::function<void(const std::string&, const py::bytes&)> write_callback;
    std::function<std::vector<std::string>(const std::string&)> list_callback;
    std::function<bool(const std::string&)> exists_callback;
    std::function<size_t(const std::string&)> size_callback;
    
public:
    DokanyVFS() : dokan_handle(nullptr), is_mounted(false) {}
    
    ~DokanyVFS() {
        if (is_mounted) {
            unmount();
        }
    }
    
    // Implementar callbacks do Dokany
    static NTSTATUS DOKAN_CALLBACK ZwCreateFile(
        LPCWSTR FileName,
        PDOKAN_IO_SECURITY_CONTEXT SecurityContext,
        ACCESS_MASK DesiredAccess,
        ULONG FileAttributes,
        ULONG ShareAccess,
        ULONG CreateDisposition,
        ULONG CreateOptions,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        // Implementação básica - permitir acesso a todos os arquivos
        DokanFileInfo->IsDirectory = FALSE;
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK ReadFile(
        LPCWSTR FileName,
        LPVOID Buffer,
        DWORD BufferLength,
        LPDWORD ReadLength,
        LONGLONG Offset,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        // Implementação básica - retornar dados vazios
        *ReadLength = 0;
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK WriteFile(
        LPCWSTR FileName,
        LPCVOID Buffer,
        DWORD NumberOfBytesToWrite,
        LPDWORD NumberOfBytesWritten,
        LONGLONG Offset,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        // Implementação básica - simular escrita
        *NumberOfBytesWritten = NumberOfBytesToWrite;
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK FindFiles(
        LPCWSTR FileName,
        PFillFindData FillFindData,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        // Implementação básica - retornar lista vazia
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK GetFileInformation(
        LPCWSTR FileName,
        LPBY_HANDLE_FILE_INFORMATION HandleFileInformation,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        // Implementação básica - arquivo padrão
        ZeroMemory(HandleFileInformation, sizeof(BY_HANDLE_FILE_INFORMATION));
        HandleFileInformation->dwFileAttributes = FILE_ATTRIBUTE_NORMAL;
        HandleFileInformation->nFileSizeLow = 0;
        HandleFileInformation->nFileSizeHigh = 0;
        
        SYSTEMTIME st;
        GetSystemTime(&st);
        SystemTimeToFileTime(&st, &HandleFileInformation->ftCreationTime);
        HandleFileInformation->ftLastAccessTime = HandleFileInformation->ftCreationTime;
        HandleFileInformation->ftLastWriteTime = HandleFileInformation->ftCreationTime;
        
        return STATUS_SUCCESS;
    }
    
    static void DOKAN_CALLBACK Cleanup(
        LPCWSTR FileName,
        PDOKAN_FILE_INFO DokanFileInfo) {
        // Cleanup básico
    }
    
    static void DOKAN_CALLBACK CloseFile(
        LPCWSTR FileName,
        PDOKAN_FILE_INFO DokanFileInfo) {
        // Close básico
    }
    
    bool mount(const std::string& drive_letter) {
        if (is_mounted) return false;
        
        mount_point = std::wstring(drive_letter.begin(), drive_letter.end());
        
        DOKAN_OPTIONS dokan_options;
        ZeroMemory(&dokan_options, sizeof(DOKAN_OPTIONS));
        dokan_options.Version = DOKAN_VERSION;
        dokan_options.MountPoint = mount_point.c_str();
        // Remover ThreadCount - não existe na versão atual
        // Usar apenas opções válidas
        dokan_options.Options = DOKAN_OPTION_CASE_SENSITIVE;
        dokan_options.Timeout = 15000; // 15 segundos
        dokan_options.AllocationUnitSize = 512;
        dokan_options.SectorSize = 512;
        
        DOKAN_OPERATIONS dokan_operations;
        ZeroMemory(&dokan_operations, sizeof(DOKAN_OPERATIONS));
        dokan_operations.ZwCreateFile = ZwCreateFile;
        dokan_operations.ReadFile = ReadFile;
        dokan_operations.WriteFile = WriteFile;
        dokan_operations.FindFiles = FindFiles;
        dokan_operations.GetFileInformation = GetFileInformation;
        dokan_operations.Cleanup = Cleanup;
        dokan_operations.CloseFile = CloseFile;
        
        // Montar em thread separada
        std::thread mount_thread([this, dokan_options, dokan_operations]() mutable {
            int status = DokanMain(&dokan_options, &dokan_operations);
            // Handle mount result
        });
        mount_thread.detach();
        
        is_mounted = true;
        return true;
    }
    
    bool unmount() {
        if (!is_mounted) return false;
        
        DokanRemoveMountPoint(mount_point.c_str());
        is_mounted = false;
        return true;
    }
    
    // Setters para callbacks Python
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
};

// Mapa global para armazenar instâncias de DokanyVFS por letra de unidade
static std::map<std::string, std::shared_ptr<DokanyVFS>> g_mounts;

// Funções globais para gerenciar montagens
bool mount_drive(const std::string& drive_letter, const std::string& backend_path) {
    // Verificar se já existe uma montagem para esta letra
    if (g_mounts.find(drive_letter) != g_mounts.end()) {
        return false;
    }
    
    // Criar nova instância
    auto vfs = std::make_shared<DokanyVFS>();
    bool success = vfs->mount(drive_letter);
    
    if (success) {
        g_mounts[drive_letter] = vfs;
    }
    
    return success;
}

bool unmount_drive(const std::string& drive_letter) {
    auto it = g_mounts.find(drive_letter);
    if (it == g_mounts.end()) {
        return false;
    }
    
    bool success = it->second->unmount();
    if (success) {
        g_mounts.erase(it);
    }
    
    return success;
}

// Função para configurar callbacks
void set_callbacks(
    const std::string& drive_letter,
    std::function<py::bytes(const std::string&)> read_cb,
    std::function<void(const std::string&, const py::bytes&)> write_cb,
    std::function<std::vector<std::string>(const std::string&)> list_cb,
    std::function<bool(const std::string&)> exists_cb,
    std::function<size_t(const std::string&)> size_cb) {
    
    auto it = g_mounts.find(drive_letter);
    if (it == g_mounts.end()) {
        throw std::runtime_error("Unidade não encontrada: " + drive_letter);
    }
    
    auto& vfs = it->second;
    if (read_cb) vfs->set_read_callback(read_cb);
    if (write_cb) vfs->set_write_callback(write_cb);
    if (list_cb) vfs->set_list_callback(list_cb);
    if (exists_cb) vfs->set_exists_callback(exists_cb);
    if (size_cb) vfs->set_size_callback(size_cb);
}

PYBIND11_MODULE(winfuse, m) {
    // Classe existente
    py::class_<DokanyVFS>(m, "DokanyVFS")
        .def(py::init<>())
        .def("mount", &DokanyVFS::mount)
        .def("unmount", &DokanyVFS::unmount)
        .def("set_read_callback", &DokanyVFS::set_read_callback)
        .def("set_write_callback", &DokanyVFS::set_write_callback)
        .def("set_list_callback", &DokanyVFS::set_list_callback)
        .def("set_exists_callback", &DokanyVFS::set_exists_callback)
        .def("set_size_callback", &DokanyVFS::set_size_callback);
    
    // Adicionar funções globais
    m.def("mount_drive", &mount_drive, "Monta uma unidade virtual");
    m.def("unmount_drive", &unmount_drive, "Desmonta uma unidade virtual");
    m.def("set_callbacks", &set_callbacks, "Configura callbacks para uma unidade montada");
}
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
#include <iostream>

// Adicionar no inicio do arquivo, apos as inclusões existentes
#include <sstream>
#include <fstream>
#include <chrono>
#include <atomic>

// Funcao de utilidade para converter wstring para string UTF-8
static std::string wstring_to_utf8(const std::wstring& wstr) {
    if (wstr.empty()) return std::string();
    
    int size_needed = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), (int)wstr.size(), NULL, 0, NULL, NULL);
    std::string str(size_needed, 0);
    WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), (int)wstr.size(), &str[0], size_needed, NULL, NULL);
    return str;
}

// Funcao de utilidade para converter LPCWSTR para string UTF-8
static std::string wchar_to_utf8(LPCWSTR wstr) {
    if (!wstr) return std::string();
    return wstring_to_utf8(std::wstring(wstr));
}

namespace py = pybind11;

// Variaveis globais para controle de erros e logging
static std::atomic<bool> g_mount_in_progress(false);
static std::atomic<bool> g_mount_success(false);
static std::string g_last_error;
static std::ofstream g_log_file;

// Funcao para logging seguro
static void log_message(const std::string& message) {
    try {
        if (!g_log_file.is_open()) {
            g_log_file.open("winfuse_log.txt", std::ios::app);
        }
        
        auto now = std::chrono::system_clock::now();
        auto now_time_t = std::chrono::system_clock::to_time_t(now);
        std::tm now_tm;
        localtime_s(&now_tm, &now_time_t);
        
        char time_str[26];
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", &now_tm);
        
        g_log_file << time_str << " - " << message << std::endl;
        g_log_file.flush();
        
        // Tambem enviar para stderr para captura pelo Python
        std::cerr << time_str << " - " << message << std::endl;
    } catch (...) {
        // Nao propagar excecões do logging
    }
}

// Declaracao antecipada da classe
class DokanyVFS;

// Mapa global para armazenar instâncias de DokanyVFS por letra de unidade
static std::map<std::string, std::shared_ptr<DokanyVFS>> g_mounts;

// Prototipos das funcões auxiliares
static DokanyVFS* GetVFSInstance(PDOKAN_FILE_INFO DokanFileInfo);
static std::string ConvertFileName(LPCWSTR FileName);

// Prototipos dos callbacks Dokany
static NTSTATUS DOKAN_CALLBACK GetVolumeInformation(
    LPWSTR VolumeNameBuffer,
    DWORD VolumeNameSize,
    LPDWORD VolumeSerialNumber,
    LPDWORD MaximumComponentLength,
    LPDWORD FileSystemFlags,
    LPWSTR FileSystemNameBuffer,
    DWORD FileSystemNameSize,
    PDOKAN_FILE_INFO DokanFileInfo);

static NTSTATUS DOKAN_CALLBACK GetDiskFreeSpace(
    PULONGLONG FreeBytesAvailable,
    PULONGLONG TotalNumberOfBytes,
    PULONGLONG TotalNumberOfFreeBytes,
    PDOKAN_FILE_INFO DokanFileInfo);

class DokanyVFS {
private:
    std::wstring mount_point;
    DOKAN_HANDLE dokan_handle;
    bool is_mounted;
    std::thread mount_thread; // Adicionar esta linha para armazenar a thread
    
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
        
        // Garantir que a thread seja encerrada
        if (mount_thread.joinable()) {
            mount_thread.join();
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
        
        DokanyVFS* vfs = GetVFSInstance(DokanFileInfo);
        if (!vfs) {
            return STATUS_UNSUCCESSFUL;
        }
        
        std::string path = ConvertFileName(FileName);
        
        // Verificar se o arquivo existe usando o callback Python
        std::lock_guard<std::mutex> lock(vfs->callbacks_mutex);
        if (vfs->exists_callback) {
            try {
                bool exists = vfs->exists_callback(path);
                DokanFileInfo->IsDirectory = FALSE; // Simplificado, deveria verificar se e diretorio
                
                // Se o arquivo nao existe e estamos tentando abri-lo para leitura, falhar
                if (!exists && !(CreateDisposition == FILE_CREATE || CreateDisposition == FILE_OPEN_IF)) {
                    return STATUS_OBJECT_NAME_NOT_FOUND;
                }
                
                return STATUS_SUCCESS;
            } catch (const std::exception& e) {
                // Lidar com excecões do Python
                return STATUS_UNSUCCESSFUL;
            }
        }
        
        // Fallback se nao houver callback
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
        
        DokanyVFS* vfs = GetVFSInstance(DokanFileInfo);
        if (!vfs) {
            *ReadLength = 0;
            return STATUS_UNSUCCESSFUL;
        }
        
        std::string path = ConvertFileName(FileName);
        
        // Ler dados usando o callback Python
        std::lock_guard<std::mutex> lock(vfs->callbacks_mutex);
        if (vfs->read_callback) {
            try {
                py::bytes data = vfs->read_callback(path);
                std::string str_data = data;
                
                // Verificar se temos dados suficientes para o offset solicitado
                if (Offset >= str_data.size()) {
                    *ReadLength = 0;
                    return STATUS_END_OF_FILE;
                }
                
                // Calcular quanto podemos ler
                size_t available = str_data.size() - Offset;
                size_t to_read = std::min<size_t>(available, BufferLength);
                
                // Copiar dados para o buffer
                memcpy(Buffer, str_data.data() + Offset, to_read);
                *ReadLength = static_cast<DWORD>(to_read);
                
                return STATUS_SUCCESS;
            } catch (const std::exception& e) {
                // Lidar com excecões do Python
                *ReadLength = 0;
                return STATUS_UNSUCCESSFUL;
            }
        }
        
        // Fallback se nao houver callback
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
        
        DokanyVFS* vfs = GetVFSInstance(DokanFileInfo);
        if (!vfs) {
            *NumberOfBytesWritten = 0;
            return STATUS_UNSUCCESSFUL;
        }
        
        std::string path = ConvertFileName(FileName);
        
        // Escrever dados usando o callback Python
        std::lock_guard<std::mutex> lock(vfs->callbacks_mutex);
        if (vfs->write_callback) {
            try {
                // Converter buffer para bytes Python
                py::bytes data(static_cast<const char*>(Buffer), NumberOfBytesToWrite);
                vfs->write_callback(path, data);
                *NumberOfBytesWritten = NumberOfBytesToWrite;
                return STATUS_SUCCESS;
            } catch (const std::exception& e) {
                // Lidar com excecões do Python
                *NumberOfBytesWritten = 0;
                return STATUS_UNSUCCESSFUL;
            }
        }
        
        // Fallback se nao houver callback
        *NumberOfBytesWritten = NumberOfBytesToWrite;
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK FindFiles(
        LPCWSTR FileName,
        PFillFindData FillFindData,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        DokanyVFS* vfs = GetVFSInstance(DokanFileInfo);
        if (!vfs) {
            return STATUS_UNSUCCESSFUL;
        }
        
        std::string path = ConvertFileName(FileName);
        
        // Listar arquivos usando o callback Python
        std::lock_guard<std::mutex> lock(vfs->callbacks_mutex);
        if (vfs->list_callback) {
            try {
                std::vector<std::string> files = vfs->list_callback(path);
                
                for (const auto& file : files) {
                    WIN32_FIND_DATAW find_data = {0};
                    
                    // Converter nome do arquivo para wchar_t
                    std::wstring wfile(file.begin(), file.end());
                    wcscpy_s(find_data.cFileName, wfile.c_str());
                    
                    // Configurar como arquivo normal
                    find_data.dwFileAttributes = FILE_ATTRIBUTE_NORMAL;
                    
                    // Obter tamanho do arquivo se possivel
                    if (vfs->size_callback) {
                        try {
                            size_t size = vfs->size_callback(path + "/" + file);
                            find_data.nFileSizeLow = static_cast<DWORD>(size & 0xFFFFFFFF);
                            find_data.nFileSizeHigh = static_cast<DWORD>(size >> 32);
                        } catch (...) {
                            // Ignorar erros ao obter tamanho
                        }
                    }
                    
                    // Preencher dados do arquivo
                    FillFindData(&find_data, DokanFileInfo);
                }
                
                return STATUS_SUCCESS;
            } catch (const std::exception& e) {
                // Lidar com excecões do Python
                return STATUS_UNSUCCESSFUL;
            }
        }
        
        // Fallback se nao houver callback
        return STATUS_SUCCESS;
    }
        
    static NTSTATUS DOKAN_CALLBACK GetFileInformation(
        LPCWSTR FileName,
        LPBY_HANDLE_FILE_INFORMATION HandleFileInformation,
        PDOKAN_FILE_INFO DokanFileInfo) {
        
        DokanyVFS* vfs = GetVFSInstance(DokanFileInfo);
        if (!vfs) {
            return STATUS_UNSUCCESSFUL;
        }
        
        std::string path = ConvertFileName(FileName);
        
        // Verificar se o arquivo existe e obter seu tamanho
        std::lock_guard<std::mutex> lock(vfs->callbacks_mutex);
        if (vfs->exists_callback && vfs->size_callback) {
            try {
                bool exists = vfs->exists_callback(path);
                if (!exists) {
                    return STATUS_OBJECT_NAME_NOT_FOUND;
                }
                
                // Configurar informacões basicas do arquivo
                ZeroMemory(HandleFileInformation, sizeof(BY_HANDLE_FILE_INFORMATION));
                HandleFileInformation->dwFileAttributes = FILE_ATTRIBUTE_NORMAL;
                
                // Obter tamanho do arquivo
                size_t size = vfs->size_callback(path);
                HandleFileInformation->nFileSizeLow = static_cast<DWORD>(size & 0xFFFFFFFF);
                HandleFileInformation->nFileSizeHigh = static_cast<DWORD>(size >> 32);
                
                // Configurar timestamps
                SYSTEMTIME st;
                GetSystemTime(&st);
                SystemTimeToFileTime(&st, &HandleFileInformation->ftCreationTime);
                HandleFileInformation->ftLastAccessTime = HandleFileInformation->ftCreationTime;
                HandleFileInformation->ftLastWriteTime = HandleFileInformation->ftCreationTime;
                
                return STATUS_SUCCESS;
            } catch (const std::exception& e) {
                // Lidar com excecões do Python
                return STATUS_UNSUCCESSFUL;
            }
        }
        
        // Fallback se nao houver callbacks
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
        // Cleanup basico
    }
    
    static void DOKAN_CALLBACK CloseFile(
        LPCWSTR FileName,
        PDOKAN_FILE_INFO DokanFileInfo) {
        // Close basico
    }
    
    bool mount(const std::string& drive_letter) {
        try {
            if (is_mounted) {
                log_message("Tentativa de montar unidade ja montada: " + drive_letter);
                return false;
            }
            
            // Verificar se a letra de unidade e valida
            if (drive_letter.empty() || drive_letter.length() > 2) {
                g_last_error = "Letra de unidade invalida: " + drive_letter;
                log_message(g_last_error);
                return false;
            }
            
            // Verificar se o driver Dokan esta instalado - usando metodo alternativo
            DWORD version = DokanDriverVersion();
            if (version == 0) {
                g_last_error = "Driver Dokan nao esta instalado ou nao pôde ser acessado";
                log_message(g_last_error);
                return false;
            }
            
            mount_point = std::wstring(drive_letter.begin(), drive_letter.end());
            
            DOKAN_OPTIONS dokan_options;
            ZeroMemory(&dokan_options, sizeof(DOKAN_OPTIONS));
            dokan_options.Version = DOKAN_VERSION;
            dokan_options.MountPoint = mount_point.c_str();
            // Configurar opcões para melhor visibilidade no Explorer
            dokan_options.Options = DOKAN_OPTION_MOUNT_MANAGER | DOKAN_OPTION_CURRENT_SESSION;
            dokan_options.Timeout = 30000; // Aumentado para 30 segundos
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
            // Adicionar mais callbacks necessarios para o Explorer
            dokan_operations.GetVolumeInformation = GetVolumeInformation;
            dokan_operations.GetDiskFreeSpace = GetDiskFreeSpace;
            
            // Montar em thread separada
            mount_thread = std::thread([this, dokan_options, dokan_operations, drive_letter]() mutable {
                try {
                    log_message("Thread de montagem iniciada para unidade " + drive_letter);
                    int status = DokanMain(&dokan_options, &dokan_operations);
                    
                    if (status != DOKAN_SUCCESS) {
                        std::stringstream ss;
                        ss << "Erro na montagem Dokany: " << status;
                        g_last_error = ss.str();
                        log_message(g_last_error);
                        is_mounted = false;
                        g_mount_success = false;
                    } else {
                        log_message("Montagem Dokany bem-sucedida para unidade " + drive_letter);
                        g_mount_success = true;
                    }
                } catch (const std::exception& e) {
                    g_last_error = "Excecao na thread de montagem: " + std::string(e.what());
                    log_message(g_last_error);
                    is_mounted = false;
                    g_mount_success = false;
                } catch (...) {
                    g_last_error = "Excecao desconhecida na thread de montagem";
                    log_message(g_last_error);
                    is_mounted = false;
                    g_mount_success = false;
                }
                
                g_mount_in_progress = false;
            });
            
            // Implementar timeout para a montagem
            auto start_time = std::chrono::steady_clock::now();
            const auto timeout = std::chrono::seconds(10); // 10 segundos de timeout
            
            // Aguardar ate que a montagem seja concluida ou timeout
            while (g_mount_in_progress && 
                   std::chrono::steady_clock::now() - start_time < timeout) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                
                // Se a montagem foi bem-sucedida, podemos sair do loop
                if (g_mount_success) {
                    break;
                }
            }
            
            // Verificar resultado apos timeout
            if (g_mount_in_progress) {
                // Ainda em progresso apos timeout
                g_last_error = "Timeout na montagem da unidade " + drive_letter;
                log_message(g_last_error);
                
                // Nao interromper a thread, apenas retornar falha
                // A thread continuara tentando montar em segundo plano
                return false;
            }
            
            if (!g_mount_success) {
                // Montagem falhou
                log_message("Falha na montagem da unidade " + drive_letter + ": " + g_last_error);
                return false;
            }
            
            // Montagem bem-sucedida
            is_mounted = true;
            log_message("Unidade " + drive_letter + " montada com sucesso");
            return true;
        } catch (const std::exception& e) {
            g_last_error = "Excecao ao montar: " + std::string(e.what());
            log_message(g_last_error);
            return false;
        } catch (...) {
            g_last_error = "Excecao desconhecida ao montar";
            log_message(g_last_error);
            return false;
        }
    }
    
    bool unmount() {
        try {
            if (!is_mounted) {
                log_message("Tentativa de desmontar unidade nao montada");
                return false;
            }
            
            std::string mp = wstring_to_utf8(mount_point);
            log_message("Iniciando desmontagem da unidade " + mp);
            
            // Tentar desmontar com timeout
            bool unmount_success = false;
            auto start_time = std::chrono::steady_clock::now();
            const auto timeout = std::chrono::seconds(15); // 15 segundos de timeout
            
            // Primeiro, tentar metodo normal
            DokanRemoveMountPoint(mount_point.c_str());
            
            // Aguardar ate que a thread termine ou timeout
            while (mount_thread.joinable() && 
                   std::chrono::steady_clock::now() - start_time < timeout) {
                // Tentar join com timeout curto para nao bloquear
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                
                // Verificar se a thread terminou
                if (!mount_thread.joinable()) {
                    unmount_success = true;
                    break;
                }
            }
            
            // Se ainda nao desmontou, tentar forcar
            if (!unmount_success) {
                log_message("Timeout na desmontagem normal, tentando forcar...");
                
                // Tentar forcar a desmontagem usando DokanUnmount
                DokanUnmount(mount_point[0]);
                
                // Aguardar mais um pouco
                std::this_thread::sleep_for(std::chrono::seconds(2));
                
                // Verificar se a thread terminou
                if (!mount_thread.joinable()) {
                    unmount_success = true;
                }
            }
            
            // Se a thread ainda estiver rodando, nao podemos fazer join seguro
            // mas podemos atualizar o estado
            is_mounted = false;
            
            if (unmount_success) {
                log_message("Unidade desmontada com sucesso");
                return true;
            } else {
                g_last_error = "Nao foi possivel desmontar completamente a unidade";
                log_message(g_last_error);
                return false;
            }
        } catch (const std::exception& e) {
            g_last_error = "Excecao ao desmontar: " + std::string(e.what());
            log_message(g_last_error);
            return false;
        } catch (...) {
            g_last_error = "Excecao desconhecida ao desmontar";
            log_message(g_last_error);
            return false;
        }
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

// Funcao auxiliar para obter a instância DokanyVFS a partir do DokanFileInfo
static DokanyVFS* GetVFSInstance(PDOKAN_FILE_INFO DokanFileInfo) {
    if (!DokanFileInfo || !DokanFileInfo->DokanOptions || !DokanFileInfo->DokanOptions->MountPoint) {
        return nullptr;
    }
    
    // Converter o ponto de montagem de wchar_t* para string
    std::wstring mount_point(DokanFileInfo->DokanOptions->MountPoint);
    std::string drive_letter = wstring_to_utf8(mount_point);
    
    auto it = g_mounts.find(drive_letter);
    if (it == g_mounts.end()) {
        return nullptr;
    }
    
    return it->second.get();
}
// Funcao auxiliar para converter caminho de wchar_t* para string
static std::string ConvertFileName(LPCWSTR FileName) {
    if (!FileName) return "";
    
    return wchar_to_utf8(FileName);
}

namespace {

    // Funcões globais para gerenciar montagens
    bool mount_drive(const std::string& drive_letter, const std::string& backend_path) {
        // Verificar se ja existe uma montagem para esta letra
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

    // Funcao para configurar callbacks
    void set_callbacks(
        const std::string& drive_letter,
        std::function<py::bytes(const std::string&)> read_cb,
        std::function<void(const std::string&, const py::bytes&)> write_cb,
        std::function<std::vector<std::string>(const std::string&)> list_cb,
        std::function<bool(const std::string&)> exists_cb,
        std::function<size_t(const std::string&)> size_cb) {
        
        auto it = g_mounts.find(drive_letter);
        if (it == g_mounts.end()) {
            throw std::runtime_error("Unidade nao encontrada: " + drive_letter);
        }
        
        auto& vfs = it->second;
        if (read_cb) vfs->set_read_callback(read_cb);
        if (write_cb) vfs->set_write_callback(write_cb);
        if (list_cb) vfs->set_list_callback(list_cb);
        if (exists_cb) vfs->set_exists_callback(exists_cb);
        if (size_cb) vfs->set_size_callback(size_cb);
    }
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
    
    // Adicionar funcões globais
    m.def("mount_drive", &mount_drive, "Monta uma unidade virtual");
    m.def("unmount_drive", &unmount_drive, "Desmonta uma unidade virtual");
    m.def("set_callbacks", &set_callbacks, "Configura callbacks para uma unidade montada");
    
    // Funcões para diagnostico e status - movidas para dentro do modulo
    m.def("get_last_error", []() { return g_last_error; }, "Retorna o ultimo erro ocorrido");
    m.def("is_mounting_in_progress", []() { return g_mount_in_progress.load(); }, "Verifica se uma montagem esta em progresso");
    m.def("check_admin_privileges", []() {
        BOOL is_admin = FALSE;
        PSID admin_group = NULL;
        SID_IDENTIFIER_AUTHORITY nt_authority = SECURITY_NT_AUTHORITY;
        
        // Criar um SID para o grupo de administradores
        if (!AllocateAndInitializeSid(&nt_authority, 2, SECURITY_BUILTIN_DOMAIN_RID,
                                     DOMAIN_ALIAS_RID_ADMINS, 0, 0, 0, 0, 0, 0, &admin_group)) {
            return false;
        }
        
        // Verificar se o processo atual esta executando como administrador
        if (!CheckTokenMembership(NULL, admin_group, &is_admin)) {
            is_admin = FALSE;
        }
        
        // Liberar o SID
        FreeSid(admin_group);
        
        return is_admin ? true : false;
    }, "Verifica se o programa esta sendo executado com privilegios de administrador");
}

// Callback para informacões de volume
static NTSTATUS DOKAN_CALLBACK GetVolumeInformation(
    LPWSTR VolumeNameBuffer,
    DWORD VolumeNameSize,
    LPDWORD VolumeSerialNumber,
    LPDWORD MaximumComponentLength,
    LPDWORD FileSystemFlags,
    LPWSTR FileSystemNameBuffer,
    DWORD FileSystemNameSize,
    PDOKAN_FILE_INFO DokanFileInfo) {
    
    // Configurar nome do volume
    wcscpy_s(VolumeNameBuffer, VolumeNameSize, L"QuarkDrive");
    
    // Configurar numero de serie
    *VolumeSerialNumber = 0x19831116;
    
    // Configurar comprimento maximo de componente
    *MaximumComponentLength = 255;
    
    // Configurar flags do sistema de arquivos
    *FileSystemFlags = FILE_CASE_SENSITIVE_SEARCH | 
                      FILE_CASE_PRESERVED_NAMES | 
                      FILE_UNICODE_ON_DISK;
    
    // Configurar nome do sistema de arquivos
    wcscpy_s(FileSystemNameBuffer, FileSystemNameSize, L"NTFS");
    
    return STATUS_SUCCESS;
}

// Callback para espaco livre em disco
static NTSTATUS DOKAN_CALLBACK GetDiskFreeSpace(
    PULONGLONG FreeBytesAvailable,
    PULONGLONG TotalNumberOfBytes,
    PULONGLONG TotalNumberOfFreeBytes,
    PDOKAN_FILE_INFO DokanFileInfo) {
    
    // Configurar espaco total (10 GB)
    *TotalNumberOfBytes = 10ULL * 1024 * 1024 * 1024;
    
    // Configurar espaco livre (5 GB)
    *FreeBytesAvailable = 5ULL * 1024 * 1024 * 1024;
    *TotalNumberOfFreeBytes = 5ULL * 1024 * 1024 * 1024;
    
    return STATUS_SUCCESS;
}
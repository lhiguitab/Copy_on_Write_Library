import os
import json
import uuid 
from datetime import datetime
import shutil
import psutil

class COWFS:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), "cow_filesystem")
        else:
            self.base_dir = base_dir

        # Directorios para datos, metadatos y log
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        self.log_path = os.path.join(self.base_dir, "cowfs.log")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        # Reiniciar el log cada vez que se crea una nueva instancia
        with open(self.log_path, 'w') as f:
            f.write("COWFS Log File\n")
            f.write("=====================\n")

        # Registro de archivos abiertos
        self.open_files = {}

        # Tamaño de bloque: 4 KB
        self.block_size = 4 * 1024

    def _log_event(self, event: str):
        # Registra un evento en el archivo de log.
        timestamp = datetime.now().isoformat()
        with open(self.log_path, 'a') as f:
            f.write(f"[{timestamp}] {event}\n")

    def _write_block(self, data: bytes) -> str:
        #Escribe un bloque de datos y retorna un ID único.
        block_id = str(uuid.uuid4())
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        with open(block_path, 'wb') as f:
            f.write(data)
        return block_id

    def _read_block(self, block_id: str) -> bytes:
        # Lee y retorna el contenido del bloque indicado.
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        with open(block_path, 'rb') as f:
            return f.read()

    def _reconstruct_content(self, blocks: list, start: int, end: int) -> bytes:
        # Reconstruye y retorna el contenido utilizando la lista de bloques y tomando en cuenta el rango [start, end].
        content_parts = []
        current_position = 0
        for block_id in blocks:
            block_path = os.path.join(self.data_dir, f"{block_id}.block")
            if os.path.exists(block_path):
                with open(block_path, 'rb') as f:
                    block_data = f.read()
                    block_start = max(0, start - current_position)
                    block_end = min(len(block_data), end - current_position)
                    content_parts.append(block_data[block_start:block_end])
                    current_position += len(block_data)
            else:
                self._log_event(f"Intento de lectura: el bloque '{block_id}' no existe.")
                return b""
        return b"".join(content_parts)

    def read(self, filename: str) -> bytes:
        # Lee y retorna el contenido completo de la última versión del archivo.
        if filename not in self.open_files:
            self._log_event(f"Error de lectura: el archivo '{filename}' no está abierto.")
            return b""
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        current_version_idx = metadata["current_version"]
        if current_version_idx < 0 or current_version_idx >= len(metadata["versions"]):
            self._log_event(f"Error de lectura: el archivo '{filename}' no tiene versiones válidas.")
            return b""
        current_version = metadata["versions"][current_version_idx]
        return self._reconstruct_content(current_version["blocks"], current_version["start"], current_version["end"])

    def read_version(self, filename: str, version: int) -> bytes:
        # Lee y retorna el contenido de una versión específica del archivo.
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        if not os.path.exists(metadata_path):
            self._log_event(f"No se encontraron metadatos para '{filename}'.")
            return b""
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        if version < 0 or version >= len(metadata["versions"]):
            self._log_event(f"La versión {version} no existe para '{filename}'.")
            return b""
        version_data = metadata["versions"][version]
        return self._reconstruct_content(version_data["blocks"], version_data["start"], version_data["end"])

    def list_blocks(self) -> list:
        # Retorna una lista con todos los bloques almacenados.
        return [f for f in os.listdir(self.data_dir) if f.endswith(".block")]

    def list_versions(self, filename: str) -> list:
        # Retorna la lista de versiones registradas para un archivo.
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        if not os.path.exists(metadata_path):
            return []
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return metadata.get("versions", [])

    def create(self, filename: str, overwrite: bool = False) -> bool:
        # Crea los metadatos iniciales para un archivo. Si ya existen y no se permite sobrescribir, se utiliza el existente.
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        if os.path.exists(metadata_path):
            if not overwrite:
                self._log_event(f"El archivo '{filename}' ya existe; no se sobrescribe.")
                return True
            else:
                os.remove(metadata_path)
                self._log_event(f"Metadatos de '{filename}' eliminados para sobrescribir.")
        metadata = {
            "filename": filename,
            "creation_time": datetime.now().isoformat(),
            "versions": [],
            "current_version": -1,
            "size": 0,
            "blocks": []
        }
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            self._log_event(f"Error al crear metadatos para '{filename}': {e}")
            return False
        self._log_event(f"Archivo '{filename}' creado exitosamente.")
        return True

    def open(self, filename: str, file_path: str = None) -> bool:
        # Abre un archivo en COWFS. Si se proporciona file_path, se trata como archivo externo: se lee su contenido, se divide en bloques y se registra en los metadatos.
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        if file_path:
            if not os.path.exists(file_path):
                self._log_event(f"El archivo externo '{file_path}' no existe.")
                return False
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                blocks = []
                content_remaining = content
                while content_remaining:
                    write_size = min(len(content_remaining), self.block_size)
                    block_id = self._write_block(content_remaining[:write_size])
                    blocks.append(block_id)
                    content_remaining = content_remaining[write_size:]
                total_size = sum(self.get_block_size(block) for block in blocks)
                metadata = {
                    "filename": filename,
                    "creation_time": datetime.now().isoformat(),
                    "versions": [{
                        "version": 0,
                        "timestamp": datetime.now().isoformat(),
                        "blocks": blocks,
                        "start": 0,
                        "end": total_size,
                        "size": total_size
                    }],
                    "current_version": 0,
                    "size": total_size,
                    "blocks": blocks
                }
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                # Registrar que el archivo es externo
                self.open_files[filename] = {
                    "metadata": metadata,
                    "position": total_size,
                    "external_file": True,
                    "file_path": file_path
                }
                self._log_event(f"Archivo externo '{file_path}' registrado como '{filename}'.")
                return True
            except Exception as e:
                self._log_event(f"Error al abrir el archivo externo '{file_path}': {e}")
                return False
        else:
            if not os.path.exists(metadata_path):
                self._log_event(f"El archivo '{filename}' no existe en COWFS.")
                return False
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                self._log_event(f"Error al abrir el archivo '{filename}': {e}")
                return False
            self.open_files[filename] = {
                "metadata": metadata,
                "position": metadata["size"]
            }
            self._log_event(f"Archivo '{filename}' abierto correctamente en COWFS.")
            return True

    def close(self, filename: str) -> bool:
        # Cierra el archivo y lo elimina del registro de abiertos.
        if filename not in self.open_files:
            return False
        del self.open_files[filename]
        self._log_event(f"Archivo '{filename}' cerrado.")
        return True

    def write(self, filename: str, data: bytes) -> int:
        #Escribe datos en el archivo generando una nueva versión. Si el archivo es externo, también actualiza el archivo físico. Retorna el número total de bytes a escribir.
        if filename not in self.open_files:
            self._log_event(f"Error de escritura: el archivo '{filename}' no está abierto.")
            return -1

        original_data = data[:]  # Se conserva para el archivo externo

        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        position = file_info["position"]
        current_version_idx = metadata["current_version"]

        if current_version_idx < 0:
            current_version = {"blocks": [], "size": 0}
        else:
            current_version = metadata["versions"][current_version_idx]

        total_bytes = len(data)
        new_size = max(position + total_bytes, current_version.get("size", 0))
        new_blocks = list(current_version.get("blocks", []))

        # Completar bloque parcial si existe
        if new_blocks:
            last_block_id = new_blocks[-1]
            last_block_data = self._read_block(last_block_id)
            if len(last_block_data) < self.block_size:
                remaining_space = self.block_size - len(last_block_data)
                to_write = data[:remaining_space]
                updated_block_data = last_block_data + to_write
                block_path = os.path.join(self.data_dir, f"{last_block_id}.block")
                with open(block_path, 'wb') as f:
                    f.write(updated_block_data)
                data = data[remaining_space:]
        # Escribir el resto en nuevos bloques
        while data:
            write_size = min(len(data), self.block_size)
            block_id = self._write_block(data[:write_size])
            new_blocks.append(block_id)
            data = data[write_size:]

        start = 0
        end = new_size
        new_version = {
            "version": len(metadata["versions"]),
            "timestamp": datetime.now().isoformat(),
            "blocks": new_blocks,
            "start": start,
            "end": end,
            "size": new_size
        }
        metadata["versions"].append(new_version)
        metadata["current_version"] = len(metadata["versions"]) - 1
        metadata["size"] = new_size
        metadata["blocks"] = new_blocks

        # Actualizar metadatos en disco
        with open(os.path.join(self.metadata_dir, f"{filename}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        file_info["position"] = new_size

        # Actualizar archivo físico si es externo
        if file_info.get("external_file"):
            external_path = file_info.get("file_path")
            try:
                with open(external_path, 'ab') as f:
                    f.write(original_data)
            except Exception as e:
                self._log_event(f"Error escribiendo en el archivo externo '{external_path}': {e}")

        self._log_event(f"Escritura en '{filename}' completada. Nueva versión: {metadata['current_version']}.")
        return total_bytes

    def undo(self, filename: str) -> bool:
        # Deshace la última acción volviendo a la versión anterior.
        if filename not in self.open_files:
            self._log_event(f"Error de undo: el archivo '{filename}' no está abierto.")
            return False
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        if metadata["current_version"] <= 0:
            self._log_event(f"Undo no disponible para '{filename}': no hay versiones anteriores.")
            return False

        # Retroceder al índice anterior
        metadata["current_version"] -= 1
        version_data = metadata["versions"][metadata["current_version"]]
        # Actualizar el tamaño y los bloques según la versión a la que se retrocede
        metadata["size"] = version_data["size"]
        metadata["blocks"] = version_data["blocks"]
        file_info["position"] = metadata["size"]

        # Guardar la metadata actualizada en disco
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        self._log_event(f"Undo ejecutado en '{filename}'. Versión actual: {metadata['current_version']}.")

        # Si se trata de un archivo externo, actualizar su contenido sobrescribiéndolo
        if file_info.get("external_file"):
            try:
                # Reconstruir el contenido de la versión actual
                content = self._reconstruct_content(version_data["blocks"], version_data["start"], version_data["end"])
                external_path = file_info.get("file_path")
                with open(external_path, 'wb') as f:
                    f.write(content)
                self._log_event(f"Archivo externo '{external_path}' actualizado tras el undo.")
            except Exception as e:
                self._log_event(f"Error al actualizar el archivo externo tras el undo: {e}")
                return False
        return True

    def get_block_size(self, block_id: str) -> int:
        # Retorna el tamaño en bytes del bloque indicado.
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        if os.path.exists(block_path):
            return os.path.getsize(block_path)
        else:
            self._log_event(f"El bloque '{block_id}' no existe.")
            return 0

    def delete_blocks(self):
        # Elimina todos los bloques almacenados.
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
            os.makedirs(self.data_dir, exist_ok=True)
            self._log_event("Todos los bloques han sido eliminados.")

    def delete_metadata(self):
        # Elimina todos los archivos de metadatos almacenados.
        if os.path.exists(self.metadata_dir):
            shutil.rmtree(self.metadata_dir)
            os.makedirs(self.metadata_dir, exist_ok=True)
            self._log_event("Todos los metadatos han sido eliminados.")

    def get_memory_usage(self) -> dict:
        # Calcula y retorna el uso actual (en bytes) de bloques y metadatos.
        total_blocks_size = 0
        total_metadata_size = 0
        if os.path.exists(self.data_dir):
            for block_file in os.listdir(self.data_dir):
                block_path = os.path.join(self.data_dir, block_file)
                if os.path.isfile(block_path):
                    total_blocks_size += os.path.getsize(block_path)
        if os.path.exists(self.metadata_dir):
            for meta_file in os.listdir(self.metadata_dir):
                meta_path = os.path.join(self.metadata_dir, meta_file)
                if os.path.isfile(meta_path):
                    total_metadata_size += os.path.getsize(meta_path)
        return {
            "total_blocks_size": total_blocks_size,
            "total_metadata_size": total_metadata_size,
            "total_size": total_blocks_size + total_metadata_size
        }

    def get_system_performance(self) -> dict:
        # Retorna información sobre el rendimiento del sistema, incluyendo memoria y uso de CPU.
        memory_info = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)
        return {
            "total_memory_gb": memory_info.total / (1024 ** 3),
            "used_memory_gb": memory_info.used / (1024 ** 3),
            "available_memory_gb": memory_info.available / (1024 ** 3),
            "memory_usage_percent": memory_info.percent,
            "cpu_usage_percent": cpu_usage
        }

    def collect_garbage(self) -> int:
        # Elimina bloques que no están referenciados en ninguna versión y retorna el número de bloques eliminados.
        referenced_blocks = set()
        for meta_file in os.listdir(self.metadata_dir):
            meta_path = os.path.join(self.metadata_dir, meta_file)
            try:
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                self._log_event(f"Error leyendo {meta_file}: {e}")
                continue
            for version in metadata.get("versions", []):
                for block in version.get("blocks", []):
                    referenced_blocks.add(block)
        removed_blocks = 0
        for block_file in os.listdir(self.data_dir):
            if block_file.endswith(".block"):
                block_id = block_file.split(".")[0]
                if block_id not in referenced_blocks:
                    os.remove(os.path.join(self.data_dir, block_file))
                    removed_blocks += 1
                    self._log_event(f"Bloque huérfano '{block_id}' eliminado.")
        self._log_event("Garbage collector ejecutado.")
        return removed_blocks
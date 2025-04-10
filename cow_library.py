import os
import json
import uuid
from datetime import datetime
from typing import Dict, List
import shutil

class COWFS:  # Librería de Copy-On-Write
    
    def __init__(self, base_dir: str = None):  # Constructor
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), "cow_filesystem")
        else:
            self.base_dir = base_dir
            
        # Aseguramos que existan los directorios necesarios
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        self.log_path = os.path.join(self.base_dir, "cowfs.log")  # Ruta del archivo de log
        
        # Crear los directorios si no existen
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Crear el archivo de log si no existe
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                f.write("COWFS Log File\n")
                f.write("=====================\n")
        
        # Inicializar el diccionario para rastrear archivos abiertos
        self.open_files = {}

        # Tamaño del bloque (por defecto 4 KB)
        self.block_size = 4 * 1024  # 4 KB
    
    def _log_event(self, event: str):
        """Registra un evento en el archivo de log."""
        timestamp = datetime.now().isoformat()
        with open(self.log_path, 'a') as f:
            f.write(f"[{timestamp}] {event}\n")

    def _write_block(self, data: bytes) -> str:  # Escribe un bloque de datos y devuelve su ID
        block_id = str(uuid.uuid4())
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        
        with open(block_path, 'wb') as f:
            f.write(data)
        
        return block_id
    
    def _read_block(self, block_id: str) -> bytes:  # Lee un bloque de datos
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        
        with open(block_path, 'rb') as f:
            return f.read()
    
    def read(self, filename: str) -> bytes:
        """
        Lee el contenido completo de la última versión de un archivo.
        :param filename: Nombre del archivo en el sistema COWFS.
        :return: Contenido del archivo como bytes.
        """
        if filename not in self.open_files:
            print(f"⚠️ El archivo '{filename}' no está abierto.")
            return b""

        file_info = self.open_files[filename]
        metadata = file_info["metadata"]

        # Obtener la última versión
        current_version_idx = metadata["current_version"]
        if current_version_idx < 0:
            print(f"⚠️ El archivo '{filename}' no tiene versiones registradas.")
            return b""

        current_version = metadata["versions"][current_version_idx]
        blocks = current_version["blocks"]
        start = current_version["start"]
        end = current_version["end"]

        # Reconstruir el contenido a partir de los bloques
        content_parts = []  # Usar una lista para almacenar los datos de los bloques
        current_position = 0
        for block_id in blocks:
            block_path = os.path.join(self.data_dir, f"{block_id}.block")
            if os.path.exists(block_path):
                with open(block_path, 'rb') as block_file:
                    block_data = block_file.read()
                    block_start = max(0, start - current_position)
                    block_end = min(len(block_data), end - current_position)
                    content_parts.append(block_data[block_start:block_end])
                    current_position += len(block_data)
            else:
                print(f"⚠️ El bloque '{block_id}' no existe.")
                return b""

        # Unir las partes al final para minimizar la copia de datos
        return b"".join(content_parts)
    
    def list_blocks(self) -> List[str]:
        """Lista todos los bloques almacenados en el sistema de archivos."""
        return [f for f in os.listdir(self.data_dir) if f.endswith(".block")]
    
    def print_all_blocks(self):
        """Imprime todos los bloques de datos almacenados en el sistema de archivos."""
        blocks = self.list_blocks()
        if not blocks:
            print("No hay bloques almacenados en el sistema.")
            return
        
        print("\n📦 Bloques almacenados en el sistema:")
        for idx, block in enumerate(blocks, 1):
            print(f"{idx}. {block}")
    
    def list_versions(self, filename: str) -> List[Dict]:
        """Lista todas las versiones de un archivo."""
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        
        if not os.path.exists(metadata_path):
            return []
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return metadata.get("versions", [])
    
    def export_to_txt(self, filename: str, output_path: str) -> bool:
        """Exporta el contenido de un archivo del sistema COWFS a un archivo .txt en el sistema operativo."""
        try:
            content = self.read(filename).decode('utf-8')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"El archivo '{filename}' se exportó correctamente a '{output_path}'.")
            return True
        except FileNotFoundError:
            print(f"El archivo '{filename}' no existe en el sistema COWFS.")
            return False
        except Exception as e:
            print(f"Error al exportar el archivo '{filename}': {e}")
            return False

    def create(self, filename: str, overwrite: bool = False) -> bool:
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        txt_path = os.path.join(self.base_dir, f"{filename}.txt")  # Ruta del archivo base .txt
        os.makedirs(self.metadata_dir, exist_ok=True)

        # Verificar si el archivo base ya existe
        if os.path.exists(txt_path):
            if not overwrite:
                print(f"⚠️ El archivo base '{txt_path}' ya existe. No se sobrescribirá.")
                # Verificar si el archivo de metadatos falta y recrearlo si es necesario
                if not os.path.exists(metadata_path):
                    print(f"⚠️ El archivo de metadatos '{metadata_path}' falta. Recreándolo...")
                    metadata = {
                        "filename": filename,
                        "creation_time": datetime.now().isoformat(),
                        "versions": [],
                        "current_version": -1,
                        "size": 0,
                        "blocks": []
                    }
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                return True  # El archivo ya existe, no es un error
            else:
                # Eliminar los archivos existentes si se permite sobrescribir
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                os.remove(txt_path)
                self._log_event(f"Archivos existentes para '{filename}' eliminados para sobrescribir.")

        # Crear los metadatos iniciales
        metadata = {
            "filename": filename,
            "creation_time": datetime.now().isoformat(),
            "versions": [],
            "current_version": -1,
            "size": 0,
            "blocks": []
        }

        # Guardar los metadatos en un archivo .json
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error al crear el archivo de metadatos '{metadata_path}': {e}")
            return False

        # Crear un archivo base .txt vacío
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("")  # Archivo vacío
        except Exception as e:
            print(f"⚠️ Error al crear el archivo base '{txt_path}': {e}")
            return False

        self._log_event(f"Archivo '{filename}' creado exitosamente.")
        print(f"✅ Archivo '{filename}' creado exitosamente con su archivo base y metadatos.")
        return True
    
    def open(self, filename: str, file_path: str = None) -> bool:
        """
        Abre un archivo existente en el sistema COWFS o un archivo externo especificando su ruta.
        Si es un archivo externo, lo registra como la versión 0 en el sistema.
        :param filename: Nombre del archivo en el sistema COWFS.
        :param file_path: Ruta completa de un archivo externo (opcional).
        :return: True si el archivo se abre correctamente, False en caso contrario.
        """
        if file_path:
            # Intentar abrir un archivo externo
            if not os.path.exists(file_path):
                print(f"⚠️ El archivo en la ruta '{file_path}' no existe.")
                return False

            try:
                # Leer el contenido del archivo externo
                with open(file_path, 'rb') as f:
                    content = f.read()

                # Dividir el contenido en bloques y almacenarlos
                blocks = []
                while content:
                    write_size = min(len(content), self.block_size)
                    block_id = self._write_block(content[:write_size])
                    blocks.append(block_id)
                    content = content[write_size:]

                # Crear los metadatos iniciales para el archivo externo
                metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
                metadata = {
                    "filename": filename,
                    "creation_time": datetime.now().isoformat(),
                    "versions": [
                        {
                            "version": 0,
                            "timestamp": datetime.now().isoformat(),
                            "blocks": blocks,
                            "start": 0,
                            "end": sum(self.get_block_size(block) for block in blocks),
                            "size": sum(self.get_block_size(block) for block in blocks)
                        }
                    ],
                    "current_version": 0,
                    "size": sum(self.get_block_size(block) for block in blocks),
                    "blocks": blocks
                }

                # Guardar los metadatos en un archivo .json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

                # Registrar el archivo como abierto
                self.open_files[filename] = {
                    "metadata": metadata,
                    "position": metadata["size"],
                    "external_file": True,
                    "file_path": file_path
                }

                print(f"✅ Archivo externo '{file_path}' registrado como '{filename}' en el sistema COWFS.")
                return True
            except Exception as e:
                print(f"⚠️ Error al abrir el archivo externo '{file_path}': {e}")
                return False
        else:
            # Abrir un archivo en el sistema COWFS
            metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")

            if not os.path.exists(metadata_path):
                print(f"⚠️ El archivo '{filename}' no existe en el sistema COWFS.")
                return False

            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Error: El archivo de metadatos '{metadata_path}' está corrupto.")
                return False

            self.open_files[filename] = {
                "metadata": metadata,
                "position": metadata["size"]
            }

            print(f"✅ Archivo '{filename}' abierto correctamente en el sistema COWFS.")
            return True
    
    def close(self, filename: str) -> bool:  # Cierra un archivo
        if filename not in self.open_files:
            return False
        
        del self.open_files[filename]
        
        return True
    
    def write(self, filename: str, data: bytes) -> int:
        """
        Escribe datos en un archivo del sistema COWFS, actualizando los bloques y el archivo físico asociado.
        :param filename: Nombre del archivo en el sistema COWFS.
        :param data: Datos a escribir en formato binario.
        :return: Número de bytes escritos, o -1 si ocurre un error.
        """
        if filename not in self.open_files:
            self._log_event(f"Intento fallido de escribir en el archivo '{filename}': no está abierto.")
            return -1

        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        position = file_info["position"]

        current_version_idx = metadata["current_version"]
        if current_version_idx < 0:
            current_version = {"blocks": [], "size": 0}
        else:
            current_version = metadata["versions"][current_version_idx]

        new_size = max(position + len(data), current_version["size"])
        new_blocks = list(current_version["blocks"])

        # Si hay un bloque parcial, completarlo primero
        if new_blocks:
            last_block_id = new_blocks[-1]
            last_block_data = self._read_block(last_block_id)

            if len(last_block_data) < self.block_size:
                remaining_space = self.block_size - len(last_block_data)
                to_write = data[:remaining_space]
                updated_block_data = last_block_data + to_write

                # Sobrescribir el bloque con los datos actualizados
                block_path = os.path.join(self.data_dir, f"{last_block_id}.block")
                with open(block_path, 'wb') as f:
                    f.write(updated_block_data)

                data = data[remaining_space:]

        # Escribir los datos restantes en nuevos bloques
        while data:
            write_size = min(len(data), self.block_size)
            block_id = self._write_block(data[:write_size])
            new_blocks.append(block_id)
            data = data[write_size:]

        # Calcular el rango de bytes para la nueva versión
        start = 0
        end = new_size

        # Actualizar metadatos del archivo
        metadata["versions"].append({
            "version": len(metadata["versions"]),
            "timestamp": datetime.now().isoformat(),
            "blocks": new_blocks,
            "start": start,
            "end": end,
            "size": new_size
        })
        metadata["current_version"] = len(metadata["versions"]) - 1
        metadata["size"] = new_size
        metadata["blocks"] = new_blocks

        with open(os.path.join(self.metadata_dir, f"{filename}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)

        file_info["position"] = new_size

        # Escribir los datos en el archivo físico asociado
        if "external_file" in file_info and file_info["external_file"]:
            # Si es un archivo externo
            file_path = file_info["file_path"]
            with open(file_path, 'ab') as f:  # Abrir en modo append binario
                f.write(data)
        else:
            # Si es el archivo base .txt
            txt_path = os.path.join(self.base_dir, f"{filename}.txt")
            with open(txt_path, 'ab') as f:  # Abrir en modo append binario
                f.write(data)

        self._log_event(f"Datos escritos en el archivo '{filename}'. Nueva versión: {metadata['current_version']}.")
        return len(data)
    
    def undo(self, filename: str) -> bool:
        if filename not in self.open_files:
            self._log_event(f"Intento fallido de deshacer cambios en el archivo '{filename}': no está abierto.")
            return False

        file_info = self.open_files[filename]
        metadata = file_info["metadata"]

        if metadata["current_version"] <= 0:
            self._log_event(f"Intento fallido de deshacer cambios en el archivo '{filename}': no hay versiones anteriores.")
            return False

        metadata["current_version"] -= 1
        metadata["size"] = metadata["versions"][metadata["current_version"]]["size"]

        with open(os.path.join(self.metadata_dir, f"{filename}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)

        self._log_event(f"Se deshicieron los cambios en el archivo '{filename}'. Versión actual: {metadata['current_version']}.")
        return True

    def get_block_size(self, block_id: str) -> int:
        """
        Obtiene el tamaño de un bloque específico.
        :param block_id: ID del bloque.
        :return: Tamaño del bloque en bytes, o None si no existe.
        """
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        if os.path.exists(block_path):
            size = os.path.getsize(block_path)
            print(f"✅ Block '{block_id}' Size: {size} bytes")
            return size
        else:
            print(f"⚠️ El bloque '{block_id}' no existe.")
            return None

    def delete_blocks(self):
        """
        Elimina todos los bloques almacenados en el sistema.
        """
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)  # Elimina el directorio 'data' y su contenido
            os.makedirs(self.data_dir, exist_ok=True)  # Recrea el directorio vacío
            print("✅ Todos los bloques han sido eliminados.")
        else:
            print("⚠️ No se encontró el directorio de bloques.")

    def delete_metadata(self):
        """
        Elimina todos los metadatos almacenados en el sistema.
        """
        if os.path.exists(self.metadata_dir):
            shutil.rmtree(self.metadata_dir)  # Elimina el directorio 'metadata' y su contenido
            os.makedirs(self.metadata_dir, exist_ok=True)  # Recrea el directorio vacío
            print("✅ Todos los metadatos han sido eliminados.")
        else:
            print("⚠️ No se encontró el directorio de metadatos.")

    def get_memory_usage(self) -> Dict[str, int]:
        """
        Calcula el uso actual de memoria de la biblioteca.
        :return: Un diccionario con el tamaño total de los bloques y los metadatos en bytes.
        """
        total_blocks_size = 0
        total_metadata_size = 0

        # Calcular el tamaño total de los bloques en el directorio 'data'
        if os.path.exists(self.data_dir):
            for block_file in os.listdir(self.data_dir):
                block_path = os.path.join(self.data_dir, block_file)
                if os.path.isfile(block_path):
                    total_blocks_size += os.path.getsize(block_path)

        # Calcular el tamaño total de los archivos de metadatos en el directorio 'metadata'
        if os.path.exists(self.metadata_dir):
            for metadata_file in os.listdir(self.metadata_dir):
                metadata_path = os.path.join(self.metadata_dir, metadata_file)
                if os.path.isfile(metadata_path):
                    total_metadata_size += os.path.getsize(metadata_path)

        # Retornar el uso de memoria en un diccionario
        return {
            "total_blocks_size": total_blocks_size,
            "total_metadata_size": total_metadata_size,
            "total_size": total_blocks_size + total_metadata_size
        }

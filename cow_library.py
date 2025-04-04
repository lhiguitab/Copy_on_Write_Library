import os
import json
import uuid
from datetime import datetime
from typing import Dict, List
import shutil

class COWFS: # Librería de Copy-On-Write
    
    def __init__(self, base_dir: str = None): # Constructor
        if base_dir is None:
            self.base_dir = os.path.join(os.getcwd(), "cow_filesystem")
        else:
            self.base_dir = base_dir
            
        # Aseguramos que existan los directorios necesarios
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        
        # Crear los directorios si no existen
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Diccionario para mantener los archivos abiertos y su información
        self.open_files = {}
        
        # Tamaño del bloque para fragmentar archivos (4KB por defecto)
        self.block_size = 4 * 1024
    
    def _write_block(self, data: bytes) -> str: # Escribe un bloque de datos y devuelve su ID
        block_id = str(uuid.uuid4())
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        
        with open(block_path, 'wb') as f:
            f.write(data)
        
        return block_id
    
    def _read_block(self, block_id: str) -> bytes: # Lee un bloque de datos
        block_path = os.path.join(self.data_dir, f"{block_id}.block")
        
        with open(block_path, 'rb') as f:
            return f.read()
    
    def read(self, filename: str) -> bytes:
        """Lee el contenido del archivo reconstruyéndolo a partir de sus bloques."""
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"El archivo '{filename}' no existe en el sistema.")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        if metadata["current_version"] < 0:
            return b""  # No hay contenido en el archivo aún
        
        version_info = metadata["versions"][metadata["current_version"]]
        file_content = b"".join(self._read_block(block) for block in version_info["blocks"])

        return file_content
    
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
    
    def create(self, filename: str) -> bool: # Crea un nuevo archivo vacío
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        if os.path.exists(metadata_path):
            return False  # El archivo ya existe
        
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
        
        return True
    
    def open(self, filename: str) -> bool: # Abre un archivo existente
        metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
        
        if not os.path.exists(metadata_path):
            return False  # El archivo no existe
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.open_files[filename] = {
            "metadata": metadata,
            "position": 0
        }
        
        return True
    
    def close(self, filename: str) -> bool: # Cierra un archivo
        if filename not in self.open_files:
            return False
        
        del self.open_files[filename]
        
        return True
    
    def write(self, filename: str, data: bytes) -> int:
        if filename not in self.open_files:
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
        
        # Actualizar metadatos del archivo
        metadata["versions"].append({
            "version": len(metadata["versions"]),
            "timestamp": datetime.now().isoformat(),
            "blocks": new_blocks,
            "size": new_size
        })
        metadata["current_version"] = len(metadata["versions"]) - 1
        metadata["size"] = new_size
        metadata["blocks"] = new_blocks
        
        with open(os.path.join(self.metadata_dir, f"{filename}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        file_info["position"] = new_size
        
        return len(data)
    
    def undo(self, filename: str) -> bool:
        if filename not in self.open_files:
            return False
        
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        
        if metadata["current_version"] <= 0:
            return False
        
        metadata["current_version"] -= 1
        metadata["size"] = metadata["versions"][metadata["current_version"]]["size"]
        
        with open(os.path.join(self.metadata_dir, f"{filename}.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
    
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


import os
import json
import uuid
from datetime import datetime
from typing import Dict, List

class COWFileSystem: # Librería de Copy-On-Write
    
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
    
    def read(self, filename: str, size: int = -1) -> bytes: # Lee datos desde el archivo abierto
        if filename not in self.open_files:
            return b''
        
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        position = file_info["position"]
        
        if metadata["current_version"] < 0:
            return b''
        
        version = metadata["versions"][metadata["current_version"]]
        blocks = version["blocks"]
        total_size = version["size"]
        
        if position >= total_size:
            return b''
        
        if size < 0 or position + size > total_size:
            size = total_size - position
        
        data = b''
        bytes_read = 0
        
        for block_id in blocks:
            block_data = self._read_block(block_id)
            remaining = size - bytes_read
            
            if remaining <= 0:
                break
            
            data += block_data[:remaining]
            bytes_read += len(block_data[:remaining])
        
        file_info["position"] += bytes_read
        
        return data
    
    def write(self, filename: str, data: bytes) -> int: # Escribe datos en el archivo, separando con espacios
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
        
        if current_version["size"] > 0:
            data = b" " + data
        
        block_index = len(new_blocks) - 1 if new_blocks else -1
        
        while data:
            write_size = min(len(data), self.block_size)
            block_id = self._write_block(data[:write_size])
            new_blocks.append(block_id)
            data = data[write_size:]
        
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

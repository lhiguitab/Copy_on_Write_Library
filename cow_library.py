import os
import json
import uuid
from datetime import datetime
from typing import Dict, List

class COWFileSystem:
    """
    Una librería que implementa mecanismos de Copy-on-Write para gestionar
    las escrituras de archivos.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Inicializa el sistema de archivos COW.
        
        Args:
            base_dir: Directorio base donde se almacenarán los archivos y sus versiones.
                     Si no se proporciona, se creará uno en el directorio actual.
        """
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
        
    def _get_metadata_path(self, filename: str) -> str:
        """Obtiene la ruta del archivo de metadatos para un archivo dado."""
        sanitized_name = self._sanitize_filename(filename)
        return os.path.join(self.metadata_dir, f"{sanitized_name}.meta.json")
    
    def _get_block_path(self, block_id: str) -> str:
        """Obtiene la ruta de un bloque de datos."""
        return os.path.join(self.data_dir, f"{block_id}.block")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitiza el nombre del archivo para uso en rutas."""
        # Reemplazar caracteres problemáticos con guiones bajos
        sanitized = os.path.basename(filename).replace('/', '_').replace('\\', '_')
        return sanitized
    
    def _generate_block_id(self) -> str:
        """Genera un ID único para un bloque de datos."""
        return str(uuid.uuid4())
    
    def _load_metadata(self, filename: str) -> Dict:
        """Carga los metadatos de un archivo."""
        metadata_path = self._get_metadata_path(filename)
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
    
    def _save_metadata(self, filename: str, metadata: Dict) -> None:
        """Guarda los metadatos de un archivo."""
        metadata_path = self._get_metadata_path(filename)
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _create_empty_metadata(self, filename: str) -> Dict:
        """Crea metadatos vacíos para un nuevo archivo."""
        return {
            "filename": filename,
            "creation_time": datetime.now().isoformat(),
            "versions": [],
            "current_version": -1,
            "size": 0
        }
    
    def _create_new_version(self, metadata: Dict, blocks: List[str], size: int) -> int:
        """
        Crea una nueva versión en los metadatos.
        
        Returns:
            El número de la nueva versión.
        """
        new_version = {
            "version": len(metadata["versions"]),
            "timestamp": datetime.now().isoformat(),
            "blocks": blocks,
            "size": size
        }
        
        metadata["versions"].append(new_version)
        metadata["current_version"] = new_version["version"]
        metadata["size"] = size
        
        return new_version["version"]
    
    def _write_block(self, data: bytes) -> str:
        """
        Escribe un bloque de datos y devuelve su ID.
        
        Args:
            data: Los datos a escribir.
            
        Returns:
            El ID del bloque creado.
        """
        block_id = self._generate_block_id()
        block_path = self._get_block_path(block_id)
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(block_path), exist_ok=True)
        
        with open(block_path, 'wb') as f:
            f.write(data)
            
        return block_id
    
    def _read_block(self, block_id: str) -> bytes:
        """
        Lee un bloque de datos.
        
        Args:
            block_id: El ID del bloque a leer.
            
        Returns:
            Los datos del bloque.
        """
        block_path = self._get_block_path(block_id)
        
        with open(block_path, 'rb') as f:
            return f.read()
    
    def create(self, filename: str) -> bool:
        """
        Crea un nuevo archivo vacío.
        
        Args:
            filename: El nombre del archivo a crear.
            
        Returns:
            True si se creó correctamente, False si ya existía.
        """
        metadata = self._load_metadata(filename)
        
        if metadata is not None:
            # El archivo ya existe
            return False
        
        # Crear metadatos vacíos
        metadata = self._create_empty_metadata(filename)
        
        # Crear versión inicial vacía
        self._create_new_version(metadata, [], 0)
        
        # Guardar metadatos
        self._save_metadata(filename, metadata)
        
        return True
    
    def open(self, filename: str) -> bool:
        """
        Abre un archivo existente.
        
        Args:
            filename: El nombre del archivo a abrir.
            
        Returns:
            True si se abrió correctamente, False si no existe.
        """
        metadata = self._load_metadata(filename)
        
        if metadata is None:
            # El archivo no existe
            return False
        
        # Guardar referencia al archivo abierto
        self.open_files[filename] = {
            "metadata": metadata,
            "position": 0
        }
        
        return True
    
    def read(self, filename: str, size: int = -1) -> bytes:
        """
        Lee datos desde la última versión del archivo.
        
        Args:
            filename: El nombre del archivo a leer.
            size: La cantidad de bytes a leer. -1 para leer todo.
            
        Returns:
            Los datos leídos o bytes vacíos si hay un error.
        """
        if filename not in self.open_files:
            return b''
        
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        position = file_info["position"]
        
        if metadata["current_version"] < 0:
            return b''
        
        # Obtener la versión actual
        version = metadata["versions"][metadata["current_version"]]
        blocks = version["blocks"]
        total_size = version["size"]
        
        # Verificar si hemos alcanzado el final del archivo
        if position >= total_size:
            return b''
        
        # Calcular cuánto leer
        if size < 0 or position + size > total_size:
            size = total_size - position
        
        # Calcular qué bloques y qué partes de ellos leer
        start_block_index = position // self.block_size
        start_block_offset = position % self.block_size
        
        end_position = position + size
        end_block_index = end_position // self.block_size
        end_block_offset = end_position % self.block_size
        
        # Leer los bloques necesarios
        data = b''
        for i in range(start_block_index, min(end_block_index + 1, len(blocks))):
            block_data = self._read_block(blocks[i])
            
            # Primer bloque (puede tener offset)
            if i == start_block_index:
                # Último bloque también
                if i == end_block_index:
                    data += block_data[start_block_offset:end_block_offset or len(block_data)]
                else:
                    data += block_data[start_block_offset:]
            # Último bloque
            elif i == end_block_index:
                data += block_data[:end_block_offset or len(block_data)]
            # Bloque intermedio
            else:
                data += block_data
        
        # Actualizar la posición
        file_info["position"] += len(data)
        
        return data
    
    def write(self, filename: str, data: bytes) -> int:
        """
        Escribe datos en el archivo, creando una nueva versión.
        
        Args:
            filename: El nombre del archivo a escribir.
            data: Los datos a escribir.
            
        Returns:
            La cantidad de bytes escritos o -1 si hay un error.
        """
        if filename not in self.open_files:
            return -1
        
        file_info = self.open_files[filename]
        metadata = file_info["metadata"]
        position = file_info["position"]
        
        # Obtener la versión actual
        current_version_idx = metadata["current_version"]
        if current_version_idx < 0:
            # No hay ninguna versión, crear una vacía
            current_version = {"blocks": [], "size": 0}
        else:
            current_version = metadata["versions"][current_version_idx]
        
        # Determinar el tamaño final del archivo
        new_size = max(position + len(data), current_version["size"])
        
        # Copiar los bloques existentes hasta la posición actual
        new_blocks = []
        bytes_copied = 0
        
        # Determinar el bloque inicial y final a modificar
        start_block_index = position // self.block_size
        
        # Copiar bloques anteriores a la posición de escritura (sin cambios)
        for i in range(min(start_block_index, len(current_version["blocks"]))):
            new_blocks.append(current_version["blocks"][i])
            bytes_copied += min(self.block_size, current_version["size"] - bytes_copied)
        
        # Si estamos escribiendo en medio de un bloque, necesitamos copiar su contenido
        if position > bytes_copied and start_block_index < len(current_version["blocks"]):
            block_data = bytearray(self._read_block(current_version["blocks"][start_block_index]))
            
            # Calcular cuántos bytes del bloque original usar
            valid_bytes = min(len(block_data), current_version["size"] - bytes_copied)
            
            # Copiar los datos del bloque existente y agregar los nuevos datos
            new_block_data = block_data[:position - bytes_copied]
            new_block_data.extend(data)
            
            # Si aún queda espacio en el bloque original después de nuestra escritura
            if position - bytes_copied + len(data) < valid_bytes:
                new_block_data.extend(block_data[position - bytes_copied + len(data):valid_bytes])
            
            # Escribir el nuevo bloque
            new_blocks.append(self._write_block(new_block_data))
            
            # Actualizar la cantidad de bytes procesados
            bytes_copied = position
            data_written = len(data)
            data = b''  # Todo el dato se ha escrito
        else:
            data_written = 0
        
        # Escribir el resto de los datos en nuevos bloques
        while data:
            block_data = data[:self.block_size]
            data = data[self.block_size:]
            
            new_blocks.append(self._write_block(block_data))
            data_written += len(block_data)
        
        # Si aún hay bloques en la versión original que no hemos procesado,
        # copiarlos si son necesarios para mantener el tamaño del archivo
        remaining_blocks_start = len(new_blocks)
        if remaining_blocks_start < len(current_version["blocks"]) and bytes_copied < current_version["size"]:
            for i in range(remaining_blocks_start, len(current_version["blocks"])):
                if bytes_copied >= new_size:
                    break
                    
                new_blocks.append(current_version["blocks"][i])
                bytes_copied += min(self.block_size, current_version["size"] - bytes_copied)
        
        # Crear nueva versión
        self._create_new_version(metadata, new_blocks, new_size)
        
        # Actualizar metadatos
        self._save_metadata(filename, metadata)
        
        # Actualizar la posición
        file_info["position"] = position + data_written
        
        return data_written
    
    def close(self, filename: str) -> bool:
        """
        Cierra un archivo.
        
        Args:
            filename: El nombre del archivo a cerrar.
            
        Returns:
            True si se cerró correctamente, False si no estaba abierto.
        """
        if filename not in self.open_files:
            return False
        
        # Simplemente eliminar la referencia
        del self.open_files[filename]
        
        return True
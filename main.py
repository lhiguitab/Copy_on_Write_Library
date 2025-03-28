from cow_library import COWFS
import shutil
import os
import json

def obtener_contenido_version(cow, filename, version):
    """Obtiene el contenido de una versión específica de un archivo."""
    metadata_path = os.path.join(cow.metadata_dir, f"{filename}.json")
    
    # Verificar si el archivo de metadatos existe
    if not os.path.exists(metadata_path):
        print(f"⚠️ No se encontraron metadatos para el archivo '{filename}'.")
        return None

    # Leer los metadatos
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Verificar si la versión solicitada existe
    if version < 0 or version >= len(metadata["versions"]):
        print(f"⚠️ La versión {version} no existe para el archivo '{filename}'.")
        return None

    # Obtener los bloques y el rango de bytes de la versión solicitada
    version_data = metadata["versions"][version]
    blocks = version_data["blocks"]
    start = version_data["start"]
    end = version_data["end"]

    # Reconstruir el contenido a partir de los bloques
    contenido = b""
    current_position = 0
    for block_id in blocks:
        block_path = os.path.join(cow.data_dir, f"{block_id}.block")
        if os.path.exists(block_path):
            with open(block_path, 'rb') as block_file:
                block_data = block_file.read()
                block_start = max(0, start - current_position)
                block_end = min(len(block_data), end - current_position)
                contenido += block_data[block_start:block_end]
                current_position += len(block_data)
        else:
            print(f"⚠️ El bloque '{block_id}' no existe.")
            return None

    return contenido


def  get_block_size(cow, block_id):
    """Obtiene el tamaño de un bloque específico."""
    block_path = os.path.join(cow.data_dir, f"{block_id}.block")
    if os.path.exists(block_path):
        size = os.path.getsize(block_path)
        print(f"✅ Block '{block_id}' Size: {size} bytes")
        return size
    else:
        print(f"⚠️ El bloque '{block_id}' no existe.")
        return None

def delete_blocks(cow):
    """Elimina todos los bloques almacenados en el sistema."""
    if os.path.exists(cow.data_dir):
        shutil.rmtree(cow.data_dir)  # Elimina el directorio 'data' y su contenido
        os.makedirs(cow.data_dir, exist_ok=True)  # Recrea el directorio vacío
        print("✅ Todos los bloques han sido eliminados.")
    else:
        print("⚠️ No se encontró el directorio de bloques.")

def delete_metadata(cow):
    """Elimina todos los metadatos almacenados en el sistema."""
    if os.path.exists(cow.metadata_dir):
        shutil.rmtree(cow.metadata_dir)  # Elimina el directorio 'metadata' y su contenido
        os.makedirs(cow.metadata_dir, exist_ok=True)  # Recrea el directorio vacío
        print("✅ Todos los metadatos han sido eliminados.")
    else:
        print("⚠️ No se encontró el directorio de metadatos.")

        

def main():

    cow = COWFS()  # Inicializar el sistema de archivos

    # delete_blocks(cow) Eliminar bloques existentes
   #delete_metadata(cow) Eliminar metadatos existentes

    filename = "mi_archivo.txt"
    version = 3
    contenido_version = obtener_contenido_version(cow, filename, version)
    
    if contenido_version is not None:
         print(f"\n📜 Contenido de la versión {version}:\n{contenido_version.decode()}")
    else:
         print(f"⚠️ No se pudo obtener el contenido de la versión {version}.")

'''
    # 1️⃣ Crear el archivo si no existe
    if cow.create(filename):
        print(f"Archivo '{filename}' creado exitosamente.")
    else:
        print(f"El archivo '{filename}' ya existe.")

    # 2️⃣ Abrir el archivo para escritura
    if cow.open(filename):
        print(f"Archivo '{filename}' abierto para escritura.")
    else:
        print(f"Error al abrir el archivo '{filename}'.")
        return

    # 3️⃣ Permitir que el usuario escriba en el archivo
    while True:
        texto = input("Escribe algo (o escribe 'salir' para terminar): ")
        if texto.lower() == "salir":
            break
        cow.write(filename, (texto + " ").encode())  
        print(f"Texto guardado en '{filename}'.")

    # 4️⃣ Leer el contenido del archivo
    cow.open(filename)  # Reabrir antes de leer
    contenido = cow.read(filename)
    print(f"\n📂 Contenido actual del archivo:\n{contenido.decode()}")

    # Listar los bloques almacenados
    print("\n📦 Bloques almacenados en el sistema:")

    blocks = cow.list_blocks()

    for block in blocks:
        block_id = block.split(".")[0]  # Obtener el ID del bloque sin la extensión
        get_block_size(cow, block_id)  # Obtener el tamaño del bloque
        


   # print("\n📜 Versiones del metadata':")
   # print(cow.list_versions(filename))

    # 5️⃣ Cerrar el archivo
    cow.close(filename)
    print(f"Archivo '{filename}' cerrado.")

    # Ruta relativa donde se guardará el archivo .txt exportado
    output_path = os.path.join(os.getcwd(), "mi_archivo_exportado.txt")

    # Exportar el archivo a un archivo .txt
    if cow.export_to_txt(filename, output_path):
        print(f"Archivo exportado correctamente en: {output_path}")
    else:
        print("Error al exportar el archivo.")

    '''

if __name__ == "__main__":
    main()

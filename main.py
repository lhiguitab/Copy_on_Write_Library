from cow_library import COWFS
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


def main():
    # Inicializar el sistema de archivos
    cow = COWFS()

    # Opcional: Eliminar bloques existentes
    cow.delete_blocks()

    # Opcional: Eliminar metadatos existentes
    cow.delete_metadata()

    filename = "corni"

    

    # Crear el archivo si no existe
    if cow.create(filename):
        print(f"Archivo '{filename}' creado exitosamente.")
    else:
        print(f"El archivo '{filename}' ya existe.")

    # Abrir el archivo para escritura
    if cow.open(filename):
        print(f"Archivo '{filename}' abierto para escritura.")
    else:
        print(f"Error al abrir el archivo '{filename}'.")
        return

    # Permitir que el usuario escriba en el archivo
    while True:
        texto = input("Escribe algo (o escribe 'salir' para terminar): ")
        if texto.lower() == "salir":
            break
        cow.write(filename, (texto + " ").encode())
        print(f"Texto guardado en '{filename}'.")

    # Leer el contenido del archivo
    contenido = cow.read(filename)
    print(f"\n📂 Contenido actual del archivo:\n{contenido.decode()}")

    # Listar los bloques almacenados
    print("\n📦 Bloques almacenados en el sistema:")
    blocks = cow.list_blocks()
    for block in blocks:
        block_id = block.split(".")[0]  # Obtener el ID del bloque sin la extensión
        cow.get_block_size(block_id)  # Obtener el tamaño del bloque

    # Cerrar el archivo
    cow.close(filename)
    print(f"Archivo '{filename}' cerrado.")

    # Exportar el archivo a un archivo .txt
    output_path = os.path.join(os.getcwd(), "mi_archivo_exportado.txt")
    if cow.export_to_txt(filename, output_path):
        print(f"Archivo exportado correctamente en: {output_path}")
    else:
        print("Error al exportar el archivo.")

    # Preguntar al usuario qué versión desea consultar
    while True:
        try:
            version = int(input("\n🔍 Ingresa el número de la versión que deseas consultar (o -1 para salir): "))
            if version == -1:
                break

            contenido_version = obtener_contenido_version(cow, filename, version)
            if contenido_version is not None:
                print(f"\n📜 Contenido de la versión {version}:\n{contenido_version.decode()}")
            else:
                print(f"⚠️ No se pudo obtener el contenido de la versión {version}.")
        except ValueError:
            print("⚠️ Por favor, ingresa un número válido.")

if __name__ == "__main__":
    main()

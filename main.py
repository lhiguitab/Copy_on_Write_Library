from cow_library import COWFS
import os
import json
import time

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
    # cow.delete_blocks()

    # Opcional: Eliminar metadatos existentes
    # cow.delete_metadata()

    filename = "corni"
    # file_path = "C:\\Users\\marti\\Downloads\\Componentes SmartCV.png"
    #"C:\\Users\\marti\\OneDrive\\Documentos\\Universidad EAFIT\\SEMESTRE IV\\Operative Systems\\TEXTO DE 4096 BYTES.docx"


    # Crear el archivo si no existe
    if not cow.create(filename):
       print(f"⚠️ El archivo '{filename}' ya existe o no se pudo crear.")
       return

    # Abrir el archivo para escritura
    if not cow.open(filename):
        print(f"⚠️ Error al abrir el archivo '{filename}'.")
        return

    print(f"Archivo '{filename}' abierto para escritura.")

    # Leer el contenido inicial del archivo
    contenido = cow.read(filename)
    print(f"\n📂 Contenido inicial del archivo:\n{contenido.decode(errors='replace')}")

    # Permitir que el usuario escriba en el archivo
    while True:
        texto = input("Escribe algo (o escribe 'salir' para terminar): ")
        if texto.lower() == "salir":
            break
        cow.write(filename, (texto + " ").encode())
        print(f"Texto guardado en '{filename}'.")

    # Leer el contenido del archivo
    contenido = cow.read(filename)

    try:
        # Intentar decodificar como texto UTF-8
        print(f"\n📂 Contenido actual del archivo:\n{contenido.decode('utf-8')}")
    except UnicodeDecodeError:
        # Si no se puede decodificar, manejarlo como binario
        print("\n📂 Contenido actual del archivo (binario):")
        print(contenido)  # Mostrar los primeros 100 bytes como ejemplo

    # Listar los bloques almacenados
    print("\n📦 Bloques almacenados en el sistema:")
    blocks = cow.list_blocks()
    for block in blocks:
        block_id = block.split(".")[0]  # Obtener el ID del bloque sin la extensión
        cow.get_block_size(block_id)  # Obtener el tamaño del bloque

    # Cerrar el archivo
    cow.close(filename)
    print(f"Archivo '{filename}' cerrado.")

    memory_usage = cow.get_memory_usage()
    print("\n📊 Uso actual de memoria:")
    print(f"  Tamaño total de bloques: {memory_usage['total_blocks_size']} bytes")
    print(f"  Tamaño total de metadatos: {memory_usage['total_metadata_size']} bytes")
    print(f"  Tamaño total: {memory_usage['total_size']} bytes")

    # Mostrar el rendimiento del sistema
    performance = cow.get_system_performance()
    print("\n📊 Rendimiento del sistema:")
    print(f"  Memoria total: {performance['total_memory']:.2f} GB")
    print(f"  Memoria usada: {performance['used_memory']:.2f} GB")
    print(f"  Memoria disponible: {performance['available_memory']:.2f} GB")
    print(f"  Porcentaje de uso de memoria: {performance['memory_usage_percent']:.2f}%")
    print(f"  Porcentaje de uso de CPU: {performance['cpu_usage_percent']:.2f}%")

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

    # Leer un archivo grande con la versión original
    start_time = time.time()
    contenido = cow.read("archivo_grande")
    end_time = time.time()
    print(f"Tiempo de lectura (original): {end_time - start_time:.2f} segundos")

    
if __name__ == "__main__":
    main()

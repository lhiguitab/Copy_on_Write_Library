from cow_library import COWFS
import os

def main():
    cow = COWFS()

    # Limpiar el entorno: eliminar bloques y metadatos previos
    cow.delete_blocks()
    cow.delete_metadata()

    print("Bienvenido al sistema COWFS combinado.")
    filename = "archivo_externo"  # Nombre interno en COWFS

    # Preguntar si se desea trabajar con un archivo externo o uno interno
    usar_externo = input("¿Deseas trabajar con un archivo externo? (s/n): ").strip().lower()
    file_path = None
    if usar_externo == "s":
        # Usa una ruta por defecto para archivo externo (modifica según tu sistema)
        #file_path = r"C:\Users\lucas\Desktop\Cuarto_Semestre\Sistemas_Operativos\Prueba.jpeg"
        #file_path = r"C:\Users\lucas\Desktop\Cuarto_Semestre\Sistemas_Operativos\Prueba.docx"
        file_path = r"C:\Users\lucas\Desktop\Cuarto_Semestre\Sistemas_Operativos\Prueba.txt"
        # Si el archivo no existe, se crea vacío para la prueba
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Contenido inicial del archivo externo.\n")
    else:
        print("Se creará un archivo interno en el sistema COWFS.")

    # Crear el archivo (metadatos)
    if not cow.create(filename):
        print(f"Error: no se pudo crear el archivo '{filename}'.")
        return

    # Abrir el archivo, usando file_path si se definió (archivo externo)
    if not cow.open(filename, file_path=file_path):
        print(f"Error al abrir el archivo '{filename}'.")
        return

    if file_path:
        print(f"\nArchivo externo '{file_path}' abierto como '{filename}' para escritura.")
    else:
        print(f"\nArchivo interno '{filename}' abierto para escritura.")

    # Mostrar el contenido inicial (según bloques)
    contenido = cow.read(filename)
    print("\nContenido inicial del archivo (desde bloques):")
    try:
        print(contenido.decode('utf-8'))
    except UnicodeDecodeError:
        print(contenido)

    # Bucle interactivo para agregar texto
    print("\nIngresa texto para agregar al archivo. Escribe 'salir' para terminar.")
    while True:
        texto = input("Texto: ")
        if texto.lower() == "salir":
            break
        cow.write(filename, (texto + "\n").encode())
        print("Texto agregado.")

    # Mostrar contenido actualizado
    contenido = cow.read(filename)
    print("\nContenido actualizado del archivo (desde bloques):")
    try:
        print(contenido.decode('utf-8'))
    except UnicodeDecodeError:
        print(contenido)

    # Listar bloques y mostrar tamaño de cada uno
    blocks = cow.list_blocks()
    print(f"\nCantidad de bloques almacenados: {len(blocks)}")
    for block in blocks:
        block_id = block.split(".")[0]
        size = cow.get_block_size(block_id)
        print(f"Bloque {block_id} - {size} bytes")

    # Mostrar uso de memoria
    memory_usage = cow.get_memory_usage()
    print("\nUso actual de memoria:")
    print(f"  Total bloques: {memory_usage['total_blocks_size']} bytes")
    print(f"  Total metadatos: {memory_usage['total_metadata_size']} bytes")
    print(f"  Uso total: {memory_usage['total_size']} bytes")

    # Listar versiones registradas
    versions = cow.list_versions(filename)
    print(f"\nVersiones registradas para '{filename}':")
    for v in versions:
        print(f"Versión {v['version']} - Tamaño: {v['size']} bytes - Timestamp: {v['timestamp']}")

    # Ejecutar garbage collector
    bloques_antes = len(cow.list_blocks())
    removed_count = cow.collect_garbage()
    bloques_despues = len(cow.list_blocks())
    print(f"\nBloques antes: {bloques_antes} - Eliminados: {removed_count} - Bloques después: {bloques_despues}")

    # Preguntar al usuario si desea deshacer la última operación
    deshacer = input("\n¿Deseas deshacer la última operación? (s/n): ").strip().lower()
    if deshacer == "s":
        if cow.undo(filename):
            print("Operación deshecha correctamente.")
        else:
            print("No fue posible deshacer la operación.")
    else:
        print("No se ejecutó deshacer.")


    # Consultar versiones específicas
    while True:
        try:
            version = int(input("\nIngresa el número de la versión a consultar (-1 para salir): "))
            if version == -1:
                break
            version_content = cow.read_version(filename, version)
            if version_content:
                print(f"\nContenido de la versión {version}:")
                try:
                    print(version_content.decode('utf-8'))
                except UnicodeDecodeError:
                    print(version_content)
            else:
                print(f"No se pudo obtener la versión {version}.")
        except ValueError:
            print("Por favor, ingresa un número válido.")

    # Mostrar rendimiento del sistema
    performance = cow.get_system_performance()
    print("\nRendimiento del sistema:")
    print(f"  Memoria total: {performance['total_memory_gb']:.2f} GB")
    print(f"  Memoria usada: {performance['used_memory_gb']:.2f} GB")
    print(f"  Memoria disponible: {performance['available_memory_gb']:.2f} GB")
    print(f"  Porcentaje de uso de memoria: {performance['memory_usage_percent']:.2f}%")
    print(f"  Porcentaje de uso de CPU: {performance['cpu_usage_percent']:.2f}%")

    # Cerrar el archivo
    cow.close(filename)
    print(f"\nArchivo '{filename}' cerrado.")

if __name__ == "__main__":
    main()
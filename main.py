from cow_library import COWFS
import shutil
import os


def main():
    # Inicializar el sistema de archivos
    cow = COWFS()

    # Opcional: Eliminar bloques existentes
    # cow.delete_blocks()

    # Opcional: Eliminar metadatos existentes
    # cow.delete_metadata()

    filename = "mi_archivo.txt"

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

if __name__ == "__main__":
    main()

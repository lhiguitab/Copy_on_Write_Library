from cow_library import COWFileSystem

def main():
    cow = COWFileSystem()  # Inicializar el sistema de archivos
    filename = "mi_archivo.txt"

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
        cow.write(filename, texto.encode())
        print(f"Texto guardado en '{filename}'.")

    # 4️⃣ Leer el contenido del archivo
    cow.open(filename)  # Reabrir antes de leer
    contenido = cow.read(filename)
    print(f"\n📂 Contenido actual del archivo:\n{contenido.decode()}")

    # 5️⃣ Cerrar el archivo
    cow.close(filename)
    print(f"Archivo '{filename}' cerrado.")

if __name__ == "__main__":
    main()

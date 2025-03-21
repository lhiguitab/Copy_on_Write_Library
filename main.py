import os
from cow_library import COWFileSystem

def print_separator():
    print("\n" + "="*50 + "\n")

def main():
    # Crear una instancia del sistema COW
    cow = COWFileSystem(base_dir="./cow_test")
    
    # Limpiar directorio si existe
    if os.path.exists("./cow_test"):
        import shutil
        shutil.rmtree("./cow_test")
    
    print("Iniciando uso de la librería COW...")
    print_separator()
    
    # Crear un nuevo archivo
    filename = "ejemplo.txt"
    print(f"Creando archivo {filename}...")
    result = cow.create(filename)
    print(f"Resultado: {'Éxito' if result else 'Error - El archivo ya existe'}")
    
    # Abrir el archivo
    print(f"\nAbriendo archivo {filename}...")
    result = cow.open(filename)
    print(f"Resultado: {'Éxito' if result else 'Error - El archivo no existe'}")
    
    # Escribir datos
    print("\nEscribiendo contenido en el archivo...")
    texto = "Hola Mundo\n"
    
    bytes_written = cow.write(filename, texto.encode())
    print(f"Bytes escritos: {bytes_written}")
    
    # Leer el contenido
    print("\nLeyendo contenido del archivo:")
    # Volver al inicio del archivo para leer desde el principio
    cow.open_files[filename]["position"] = 0  
    content = cow.read(filename).decode()
    print(f"---\n{content}---")
    
    # Añadir más contenido al final
    print("\nAñadir Algo al .txt\n")
    texto_adicional = "\nHello World\n"
    # Mover posición al final
    cow.open_files[filename]["position"] = len(texto.encode())
    bytes_written = cow.write(filename, texto_adicional.encode())
    print(f"Bytes adicionales escritos: {bytes_written}")
    
    # Leer todo el contenido actualizado
    print("\nLeyendo contenido actualizado:")
    cow.open_files[filename]["position"] = 0
    content = cow.read(filename).decode()
    print(f"---\n{content}---")
    
    # Cerrar el archivo
    print("\nCerrando archivo...")
    cow.close(filename)
    print("Archivo cerrado con éxito.")
    
    print_separator()
    print("Ejemplo completado con éxito.")

if __name__ == "__main__":
    main()
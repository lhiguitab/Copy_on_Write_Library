# COWFS - Copy-On-Write File System Library

<div align="center">
  <h3>Universidad EAFIT</h3>
  <h4>SI2004-6963 Operating Systems</h4>
  <h4>Project #2: File Versioning Management Library</h4>
  <br>
  <p><strong>Authors:</strong> Juan Pablo Corena, Lucas Higuita Bedoya, Martin Vanegas Ospina</p>
</div>

## 📑 Table of Contents
- [Abstract](#abstract)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Example Workflow](#example-workflow)
- [Technical Details](#technical-details)

## Abstract
The Copy-On-Write File System (COWFS) is a Python-based library designed to efficiently manage file versions using the Copy-On-Write (COW) technique. This system divides file data into fixed-size blocks (4 KB by default) and tracks changes incrementally, allowing for efficient storage and retrieval of file versions.

COWFS provides essential features such as file creation, reading, writing, closing, and version control. It also includes tools for memory usage analysis, block management, and metadata handling. The library is ideal for applications requiring versioned file systems, efficient memory usage, and robust data management.

## Installation
### Requirements
- Python 3.12.10 or higher
- psutil 7.0.0

```bash
# Install psutil dependency
pip install psutil==7.0.0

# Clone the repository
git clone https://github.com/lhiguitab/Copy_on_Write_Library.git
cd Copy_on_Write_Library
```
## Getting Started
### Initialize Cow Library 

```python
# Import the library
from cow_library import COWFS

# Initialize the COWFS system
cow = COWFS()  # Creates necessary directories automatically
```
This initialization creates the following directory structure:

- data/: For storing data blocks

- metadata/: For storing file metadata information

- cowfs.log: Log file to track operations

### Usage Guide
#### 1. Create a New File

```python
# Create a new file in the COWFS system
if cow.create("myFile"):
    print("File created successfully.")
else:
    print("File already exists or creation failed.")
```
This creates:
 - A plain .txt file in the project path
 - An associated metadata.json file to track versions and blocks

#### 2. Open Files

Open an Existing COWFS File
```python
if cow.open("myFile"):
    print("File opened successfully.")
else:
    print("Error: File does not exist in COWFS.")
```
Open an External File

```python
file_path = "C:\\path\\to\\your\\file.txt"  # Can be any file type (.txt, .jpg, .docx, etc.)

if cow.open("importedFile", file_path=file_path):
    print(f"File opened successfully from path '{file_path}'.")
else:
    print(f"Error: Could not open file from path '{file_path}'.")
```
#### 3. Write Data to Files
Writing requires data to be in bytes format:

```python
# Use the b prefix for string literals or convert strings to bytes
cow.write("myFile", b"Hello, world!")

# Add more content
cow.write("myFile", b"This is a second line.\n")

# Convert string to bytes for writing
text = "Dynamic text content"
cow.write("myFile", text.encode('utf-8'))
```
#### 4. Read File Content
```python

# Read content from the latest version
content = cow.read("myFile")

# Convert bytes to string for display
print(content.decode('utf-8'))
```
#### 5. Version Control

##### Undo Changes
```python
# Revert to the previous version
if cow.undo("myFile"):
    print("Changes undone successfully.")
else:
    print("No previous versions to undo.")
```
##### List File Versions
```python
# Get all versions of a file
versions = cow.list_versions("myFile")
print("File versions:", versions)
```
#### 6. Close Files
```python
# Close file when done
cow.close("myFile")
```
#### 7. System Management

##### Delete All Blocks
```python
# Remove all data blocks
cow.delete_blocks()
print("All blocks have been deleted.")
```
##### Delete All Metadata
```python
# Remove all metadata files
cow.delete_metadata()
print("All metadata has been deleted.")
```
##### List Blocks
```python
# View all blocks in the system
blocks = cow.list_blocks()
print("Blocks in the system:", blocks)
# Prettier display
cow.print_all_blocks()
```
##### Get Block Size
```python
block_id = "your_block_id_here"
size = cow.get_block_size(block_id)
if size is not None:
    print(f"Block size: {size} bytes")
```
##### Memory Usage Analysis
```python
# Get memory statistics
memory_usage = cow.get_memory_usage()
print(f"Total blocks size: {memory_usage['total_blocks_size']} bytes")
print(f"Total metadata size: {memory_usage['total_metadata_size']} bytes")
print(f"Total size: {memory_usage['total_size']} bytes")
```
##### System Performance
```python
# Get system performance metrics
performance = cow.get_system_performance()
print(f"Total memory: {performance['total_memory']:.2f} GB")
print(f"Used memory: {performance['used_memory']:.2f} GB")
print(f"Available memory: {performance['available_memory']:.2f} GB")
print(f"Memory usage: {performance['memory_usage_percent']}%")
print(f"CPU usage: {performance['cpu_usage_percent']}%")
```
## API Reference

### Constructor
```python
COWFS(base_dir: str = None)
```
Initializes the Copy-On-Write file system.

 Parameters:

- base_dir (str, optional): Base directory for the file system. If not provided, the current working directory is used.

 Details:

  - Creates directories for data blocks and metadata
  
  - Initializes logging system
  
  - Sets block size to 4 KB by default

Example:

```python
cow = COWFS(base_dir="C:\\my_cow_filesystem")
```
### Core Functions
#### Create
```bash
create(filename: str, overwrite: bool = False) -> bool
```
Creates a new file in the COWFS system.

Parameters:

 - filename (str): Name of the file to create
  
 - overwrite (bool): If True, overwrites existing file; default is False
  
Returns:
  
  - bool: True if file created successfully, False otherwise

Example:

```python
if cow.create("document"):
    print("File created successfully.")
```
#### Open
```bash
open(filename: str, file_path: str = None) -> bool
```
 Opens an existing file in the COWFS system or imports an external file.

Parameters:

  - filename (str): Name to use in the COWFS system
  
  - file_path (str, optional): Path to external file to import

Returns:

  bool: True if file opened successfully, False otherwise

Example:

```python
cow.open("document")
# or
cow.open("imported_image", file_path="C:\\pictures\\photo.jpg")
```
#### Write
```bash
write(filename: str, data: bytes) -> int
```

 Writes data to a file, creating a new version.

Parameters:

  - filename (str): Name of the file to write to
  
  - data (bytes): Data to write to the file

Returns:

  - int: Number of bytes written, or -1 if error occurred

Example:

```python
bytes_written = cow.write("document", b"New content")
```
#### Read
```bash
read(filename: str) -> bytes
```
 Reads content from the current version of a file.

 Parameters:

   - filename (str): Name of the file to read

 Returns:

    - bytes: File content as bytes

Example:

```python

content = cow.read("document")
print(content.decode('utf-8'))
```
#### Close
```bash
close(filename: str) -> bool
```
Closes an open file.

 Parameters:

  -filename (str): Name of the file to close

 Returns:

  - bool: True if file closed successfully, False if not open

Example:

```python

cow.close("document")
```
### Version Control
#### Undo
```bash
undo(filename: str) -> bool
```
Reverts file to the previous version.

 Parameters:

  - filename (str): Name of the file

 Returns:

  - bool: True if changes undone successfully, False if no previous versions

Example:

```python
cow.undo("document")
```
#### List Versions
```bash
list_versions(filename: str) -> List[Dict]
```
 Lists all versions of a file.

 Parameters:

  - filename (str): Name of the file

 Returns:

  - List[Dict]: List of version dictionaries with metadata

Example:
```python

versions = cow.list_versions("document")
```

### System Management Functions
#### List Blocks
```bash
list_blocks() -> List[str]
```
Lists all blocks in the system.

 Returns:

  - List[str]: List of block IDs

Example:
```python

blocks = cow.list_blocks()
```
#### Print all blocks 
```bash
print_all_blocks()
```
Prints all blocks stored in the system.

Example:

```python
cow.print_all_blocks()
```
#### Get Block Size
```bash
get_block_size(block_id: str) -> int
```

Gets the size of a specific block.

 Parameters:

  - block_id (str): ID of the block

 Returns:

  - int: Size of the block in bytes, or None if not found

Example:
```python

size = cow.get_block_size("block_id_here")
```
#### Delete Blocks
```bash
delete_blocks()
```
Deletes all data blocks in the system.

Example:
```python
cow.delete_blocks()
```
#### Delete Metadata
```bash
delete_metadata()
```
Deletes all metadata files in the system.

Example:
```python
cow.delete_metadata()
```
#### Get Memory Usage 
```bash
get_memory_usage() -> Dict[str, int]
```
Calculates current memory usage of the library.

 Returns:

  - Dict[str, int]: Dictionary with memory usage statistics

Example:

```python
memory_usage = cow.get_memory_usage()
```
#### Get System Performance
```bash
get_system_performance() -> Dict[str, float]
```
Gets information about system performance.

 Returns:

  - Dict[str, float]: Dictionary with system performance metrics

Example:
```python
performance = cow.get_system_performance()
```
### Internal Functions
#### .log
```bash
_log_event(event: str)
```
Logs an event to the system log file.
#### Write Block 
```bash
_write_block(data: bytes) -> str
```
Writes a block of data and returns its ID.
#### Read Block
```bash
_read_block(block_id: str) -> bytes
```
Reads a data block by its ID.

### Example Workflow
Below is a complete example demonstrating how to use the COWFS library:

```python

from cow_library import COWFS

# Initialize the system
cow = COWFS()

# Create a file
filename = "myDocument"
if cow.create(filename):
    print("File created successfully.")

# Write data to the file
cow.write(filename, b"Hello, world!\n")
cow.write(filename, b"This is the second line.\n")

# Read the file content
content = cow.read(filename)
print("File content:")
print(content.decode('utf-8'))

# List all blocks
cow.print_all_blocks()

# Get memory usage
memory_usage = cow.get_memory_usage()
print(f"Total memory used: {memory_usage['total_size']} bytes")

# Undo the last change
if cow.undo(filename):
    print("Last change undone.")
    
# Read the file content again after undo
content = cow.read(filename)
print("File content after undo:")
print(content.decode('utf-8'))

# Close the file
cow.close(filename)
Technical Details
Block Structure
Files are divided into blocks of 4 KB by default. Each block is stored as a separate file in the data/ directory with a UUID as its identifier.
```

### Technical Details
File metadata is stored in JSON format with the following structure:

```json

{
  "filename": "example",
  "creation_time": "2023-04-10T15:30:45.123456",
  "versions": [
    {
      "version": 0,
      "timestamp": "2023-04-10T15:30:45.123456",
      "blocks": ["block_id_1", "block_id_2"],
      "start": 0,
      "end": 8192,
      "size": 8192
    },
    {
      "version": 1,
      "timestamp": "2023-04-10T15:35:12.654321",
      "blocks": ["block_id_1", "block_id_3"],
      "start": 0,
      "end": 10240,
      "size": 10240
    }
  ],
  "current_version": 1,
  "size": 10240,
  "blocks": ["block_id_1", "block_id_3"]
}
```
### Copy-On-Write Implementation

When modifying a file, COWFS follows these steps:

 - Read the current blocks list from metadata
  
 - Create new blocks for modified content
  
 - Create a new version entry with references to unchanged blocks and new blocks
  
 - Update the current version pointer in metadata

This approach ensures that:

 - Original data is never modified
  
 - Storage efficiency is maintained by reusing unchanged blocks
  
 - Previous versions are always accessible
  
 - Operations can be undone easily

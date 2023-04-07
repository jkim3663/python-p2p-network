import os

dir_path = "./"

# Delete files in folder1
if os.path.exists(os.path.join(dir_path, "folder1", "chunk_2")):
    os.remove(os.path.join(dir_path, "folder1", "chunk_2"))
if os.path.exists(os.path.join(dir_path, "folder1", "chunk_3")):
    os.remove(os.path.join(dir_path, "folder1", "chunk_3"))

# Delete files in folder2
if os.path.exists(os.path.join(dir_path, "folder2", "chunk_1")):
    os.remove(os.path.join(dir_path, "folder2", "chunk_1"))
if os.path.exists(os.path.join(dir_path, "folder2", "chunk_4")):
    os.remove(os.path.join(dir_path, "folder2", "chunk_4"))

# Delete files in folder3
if os.path.exists(os.path.join(dir_path, "folder3", "chunk_2")):
    os.remove(os.path.join(dir_path, "folder3", "chunk_2"))
if os.path.exists(os.path.join(dir_path, "folder3", "chunk_4")):
    os.remove(os.path.join(dir_path, "folder3", "chunk_4"))

# Delete files in folder4
if os.path.exists(os.path.join(dir_path, "folder4", "chunk_1")):
    os.remove(os.path.join(dir_path, "folder4", "chunk_1"))
if os.path.exists(os.path.join(dir_path, "folder4", "chunk_3")):
    os.remove(os.path.join(dir_path, "folder4", "chunk_3"))

# Delete logs.log in PA2 folder
if os.path.exists(os.path.join(dir_path, "logs.log")):
    os.remove(os.path.join(dir_path, "logs.log"))

# with open(cwd + '/folder4/chunk_4', 'rb') as f:
#     file = f.read()
#     print(len(file) // 1048576 + 1)
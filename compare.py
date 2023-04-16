import filecmp
import os

dir_path = "./"

chunk_1_from_folder_1 = os.path.join(dir_path, "folder1", "chunk_1")
chunk_2_from_folder_1 = os.path.join(dir_path, "folder1", "chunk_2")
chunk_3_from_folder_1 = os.path.join(dir_path, "folder1", "chunk_3")
chunk_4_from_folder_1 = os.path.join(dir_path, "folder1", "chunk_4")

for i in range(2, 5):
    folder_name = "folder" + str(i)

    if os.path.exists(os.path.join(dir_path, folder_name, "chunk_1")):
        file_1 = os.path.join(dir_path, folder_name, "chunk_1")
        print(f'{i}->1: {filecmp.cmp(file_1, chunk_1_from_folder_1)}')

    if os.path.exists(os.path.join(dir_path, folder_name, "chunk_2")):
        file_2 = os.path.join(dir_path, folder_name, "chunk_2")
        print(f'{i}->2: {filecmp.cmp(file_2, chunk_2_from_folder_1)}')

    if os.path.exists(os.path.join(dir_path, folder_name, "chunk_3")):
        file_3 = os.path.join(dir_path, folder_name, "chunk_3")
        print(f'{i}->3: {filecmp.cmp(file_3, chunk_3_from_folder_1)}')

    if os.path.exists(os.path.join(dir_path, folder_name, "chunk_4")):
        file_4 = os.path.join(dir_path, folder_name, "chunk_4")
        print(f'{i}->4: {filecmp.cmp(file_4, chunk_4_from_folder_1)}')
    
    print()    
    
 




# filecmp.cmp('file1.txt', 'file1.txt')
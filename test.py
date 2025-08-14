import os

folder_path = r"C:\Users\ADMIN\Downloads"  # hoặc đường dẫn tới folder bạn muốn xem

for item in os.listdir(folder_path):
    print(item)

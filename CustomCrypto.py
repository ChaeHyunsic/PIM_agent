from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import os
import os.path

def encrypt(file_name, nickname):
    original_password = nickname.encode('utf8') #username으로 설정
    key = hashlib.pbkdf2_hmac(
        hash_name='sha256', password=original_password, salt=b'$3kj##agh_', iterations=100000)
    Block_Size = 16
    
    
    with open(file_name, 'rb') as fo:
        text = fo.read()
    # 파일 읽기
    aes = AES.new(key, AES.MODE_ECB)
    padded_text = pad(text, Block_Size)
    encrypted_text = aes.encrypt(padded_text)
    with open(file_name + ".enc", 'wb') as fo:
        fo.write(encrypted_text)
        os.remove(file_name)


def decrypt(file_name, nickname):
    original_password = nickname.encode('utf8') #username으로 설정
    key = hashlib.pbkdf2_hmac(
        hash_name='sha256', password=original_password, salt=b'$3kj##agh_', iterations=100000)
    Block_Size = 16

    with open(file_name, 'rb') as fo:
        ciphertext = fo.read()
    aes = AES.new(key, AES.MODE_ECB)
    decrypted_text = aes.decrypt(ciphertext)
    unpadded_text = unpad(decrypted_text, Block_Size)
    with open(file_name[:-4], 'wb') as fo:
        fo.write(unpadded_text)
        os.remove(file_name)


def getAllFiles(filepath):
    dirs = []

    for (root, directories, files) in os.walk(filepath):
        for file in files:
            file_path = os.path.join(root, file)
            dirs.append(file_path)

    return dirs


def encrypt_all_files(filepath, nickname):
    dirs = getAllFiles(filepath)
    for file_name in dirs: 
        if file_name[-4:] != ".enc":
            encrypt(file_name, nickname)

    return True


def decrypt_all_files(filepath, nickname):
    dirs = getAllFiles(filepath)
    for file_name in dirs:
        if file_name[-4:] == ".enc":
            decrypt(file_name, nickname)

    return True
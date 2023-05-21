from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import os
import os.path

# 파일을 암호화 하기 위한 메서드 
def encrypt(file_name, nickname):
    original_password = nickname.encode('utf8')                                                 # 닉네임을 UTF-8로 인코딩하여 비밀번호로 사용
    key = hashlib.pbkdf2_hmac(                                                                  # sha-256 해시함수를 사용해 hmac으로 키를 생성
        hash_name='sha256', password=original_password, salt=b'$3kj##agh_', iterations=100000) 
    Block_Size = 16                                                                             # 블록 크기를 16으로 설정
    
    with open(file_name, 'rb') as fo:                                                           # 주어진 파일을 바이너리 모드로 열고 fo에 할당
        text = fo.read()                                                                        # 파일 읽기
    
    iv = b'trvvIlnENsHxyqKp'                                                                    # 초기화 벡터(IV)를 설정
    aes = AES.new(key, AES.MODE_CBC, iv)                                                        # AES 객체 생성 (CBC모드)
    padded_text = pad(text, Block_Size)                                                         # 패딩을 적용
    encrypted_text = aes.encrypt(padded_text)                                                   # 암호화된 텍스트를 생성
                                
    with open(file_name + ".enc", 'wb') as fo:                                                  
        fo.write(encrypted_text)                                                                # 암호화된 텍스트를 파일에 기록
        os.remove(file_name)                                                                    # 원본 파일을 삭제

# 파일을 복호화하기 위한 메서드 
def decrypt(file_name, nickname):
    original_password = nickname.encode('utf8')                                                 # 닉네임을 UTF-8로 인코딩하여 비밀번호로 사용
    key = hashlib.pbkdf2_hmac(                                                                  # sha-256 해시함수를 사용해 hmac으로 키를 생성
        hash_name='sha256', password=original_password, salt=b'$3kj##agh_', iterations=100000)
    Block_Size = 16                                                                             # 블록 크기를 16으로 설정

    with open(file_name, 'rb') as fo:                                                           # 주어진 파일을 바이너리 모드로 열고 fo에 할당
        ciphertext = fo.read()                                                                  # 파일을 읽어 암호문 얻음

    iv = b'trvvIlnENsHxyqKp'                                                                    # 초기화 벡터(IV)를 설정
    aes = AES.new(key, AES.MODE_CBC, iv)                                                        # AES 객체를 생성 (CBC모드)
    decrypted_text = aes.decrypt(ciphertext)                                                    # 복호화된 텍스트를 얻음
    unpadded_text = unpad(decrypted_text, Block_Size)                                           # 패딩을 제거

    with open(file_name[:-4], 'wb') as fo:                                                      
        fo.write(unpadded_text)                                                                 # 복호화된 텍스트를 파일에 기록
        os.remove(file_name)                                                                    # 암호화된 파일을 삭제

# 지정된 경로를 탐색하면서 모든 파일의 경로를 얻어오기 위한 메서드 
def getAllFiles(filepath):
    dirs = []                                                           # 파일 경로를 저장하기 위한 빈 리스트를 생성

    for (root, directories, files) in os.walk(filepath):                # 지정된 경로 탐색
        for file in files:
            file_path = os.path.join(root, file)                        # 파일의 경로를 생성
            dirs.append(file_path)                                      # 파일의 경로를 리스트에 추가

    return dirs

# 지정된 경로를 탐색하면서 모든 파일을 암호화 하기위한 메서드 
def encrypt_all_files(filepath, nickname):
    dirs = getAllFiles(filepath)                        # 암호화 하기위한 모든 파일의 경로을 얻음
    
    for file_name in dirs:                              # 모든 경로 탐색
        if file_name[-4:] != ".enc":                    # 암호화 되지 않은 파일인 경우
            encrypt(file_name, nickname)                # 파일 암호화

# 지정된 경로를 탐색하면서 모든 파일을 복호화 하기위한 메서드 
def decrypt_all_files(filepath, nickname):
    dirs = getAllFiles(filepath)                        # 복호화 하기위한 모든 파일의 경로을 얻음

    for file_name in dirs:                              # 모든 경로 탐색
        if file_name[-4:] == ".enc":                    # 복호화 되지 않은 파일인 경우
            decrypt(file_name, nickname)                # 파일 복호화
            
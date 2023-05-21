import os
import shutil
import random
import math
import time

from CustomCrypto import decrypt_all_files

# 컨트롤 파일 경로 반환 메서드 
def getControlDataNames(nickname, member_setting):
    if(nickname == None):                                           # 비회원일 경우
        member_setting = [1,1,1,1,1,1,1]                            # 전체 파일 리스트 반환

    controlDataNames = []                           

    if member_setting[0] == 1:                                                              # 북마크 파일 경로 추가
        controlDataNames.extend(["/Bookmarks", "/Bookmarks.bak"])           
    if member_setting[1] == 1:                                                              # 방문기록 파일 경로 추가
        controlDataNames.extend(["/History", "/History-journal", "/Visited Links"])  
    if member_setting[2] == 1:                                                              # 다운로드 기록 파일 경로 추가
        controlDataNames.extend(["/DownloadMetadata"])  
    if member_setting[3] == 1:                                                              # 로그인, 자동완성 양식 파일 경로 추가
        controlDataNames.extend(["/Login Data", "/Login Data For Account", "/Login Data-journal", "/Preferences", "/Shortcuts", 
                                    "/Shortcuts-journal", "/Top Sites", "/Top Sites-journal", "/Web Data", "/Web Data-journal", 
                                    "/Local State", "/IndexedDB", "/Storage", "/Sync App Settings", "/Sync Data", "/WebStorage"])  

    return controlDataNames

# 삭제할 파일 경로 반환 메서드 
def getRemoveDataNames(nickname, member_setting):
    if(nickname == None):                                                   # 비회원일 경우
        member_setting = [1,1,1,1,1,1,1]                                    # 전체 파일 리스트 반환

    removeDataNames = []

    if member_setting[4] == 1:                                              # 쿠키 파일 경로 추가
        removeDataNames.extend(["/Cookies"])    
    if member_setting[5] == 1:                                              # 캐시 파일 경로 추가
        removeDataNames.extend(["/cache", "/Code cache", "DawnCache"])  
    if member_setting[6] == 1:                                              # 세션 파일 경로 추가
        removeDataNames.extend(["/Session Storage", "/Sessions"])  

    return removeDataNames

# 크롬 브라우저를 사용 시 개인정보 파일들이 저장된 원본 경로 반환 메서드 
def getSrcPath():
    homePath = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default').replace('\\', '/')     # 사용자 홈 디렉터리를 기준

    return homePath

# 사용자의 폴더로 개인정보 파일들을 이동시킬 경로 반환 메서드 
def getDstPath(nickname):
    dstPath = os.path.expanduser('~/AppData/Local/PIM_AGENT/').replace('\\', '/') + nickname            # 사용자 홈 디렉터리를 기준

    return dstPath

# 에이전트를 실행했을 때 개인정보를 관리할 루트 폴더 생성 메서드 
def initCheck():
    dirPath = os.path.expanduser('~/AppData/Local/PIM_AGENT').replace('\\', '/')                        # 사용자 홈 디렉터리를 기준

    if(not os.path.isdir(dirPath)):
        os.mkdir(dirPath)

# 사용자 로그인 시 로컬 폴더가 없다면 생성하고 암호화된 파일 복호화한 뒤 원본 경로로 이동시키는 메서드 
def initLocalCheck(nickname, member_setting):
    srcPath = getSrcPath()                                                                              # 소스 경로 할당
    dstPath = os.path.expanduser('~/AppData/Local/PIM_AGENT/').replace('\\', '/') + nickname            # 사용자 홈 디렉터리를 기준

    if(not os.path.isdir(dstPath)):                 # 폴더가 없을 경우
        os.mkdir(dstPath)                           # 사용자 폴더 생성
        
    time.sleep(0.5)                                 # 시그널 emit 동기화
    decrypt_all_files(dstPath, nickname)            # 암호화 되어있는 모든 파일 복호화

    memberFileMove(dstPath, srcPath, nickname, member_setting)          # 사용자 설정 조건에 맞는 파일 이동
    

# 사용자 설정 조건에 맞는 파일 이동 메서드 
def memberFileMove(srcPath, dstPath, nickname, member_setting):
    filenames = getControlDataNames(nickname, member_setting)           # 이동시킬 파일들의 경로를 리스트 형태로 획득

    for filename in filenames:
        if(os.path.isfile(srcPath + filename)):                         # 원본 경로에 파일이 있을 경우 
            if(os.path.exists(dstPath + filename)):                     # 목적지 경로에 기존 파일이 존재하는 경우
                os.remove(dstPath + filename)                           # 기존 파일 삭제
            shutil.move(srcPath + filename, dstPath + filename)         # 파일 이동

        elif(os.path.isdir(srcPath + filename)):                        # 원본 경로에 폴더가 있을 경우
            if(os.path.exists(dstPath + filename)):                     # 목적지 경로에 기존 폴더가 존재하는 경우
                shutil.rmtree(dstPath + filename)                       # 기존 폴더 삭제
            shutil.move(srcPath + filename, dstPath + filename)         # 폴더 이동

# 로그인 된 상태에서 원본 경로의 파일, 폴더를 삭제하고 멀티 프로필을 삭제하는 메서드 
def memberFileRemove(srcPath, nickname, member_setting):
    filenames = getRemoveDataNames(nickname, member_setting)            # 삭제할 파일 리스트
    multiProfilePath = srcPath.replace('\\', '/')[:-8]                  # 멀티 프로필 경로
    multiProfilenames = getMultiProfilenames()                          # 멀티 프로필 리스트

    for filename in filenames:  
        if(os.path.isfile(srcPath + filename)):                         # 원본 경로에 파일이 있을 경우
            os.remove(srcPath + filename)                               # 파일 삭제

        elif(os.path.isdir(srcPath + filename)):                        # 원본 경로에 폴더가 있을 경우
            shutil.rmtree(srcPath + filename)                           # 폴더 삭제

    i = 1                                                   
    while(os.path.exists(multiProfilePath + multiProfilenames[0] + str(i))):        # 멀티프로필 폴더가 존재할 경우
        shutil.rmtree(multiProfilePath + multiProfilenames[0] + str(i))             # 폴더 삭제
        if(os.path.exists(multiProfilePath + multiProfilenames[1])):                # Local State 파일이 존재할 경우
            os.remove(multiProfilePath + multiProfilenames[1])                      # 해당 파일 삭제
        i += 1                                                                      # 모든 멀티 프로필을 삭제하기 위해 순회

# 비 로그인 상태에서 원본 경로의 파일, 폴더를 삭제하고 멀티 프로필을 삭제하는 메서드 
def guestFileRemove(srcPath, flag):
    multiProfilePath = srcPath.replace('\\', '/')[:-8]                      # 다중 프로필 경로
    multiProfilenames = getMultiProfilenames()                              # 멀티 프로필 리스트

    if(flag == 0):                                                          # 북마크, 방문기록, 다운로드, 로그인 파일들의 경로 지정
        filenames = getControlDataNames(None, None)
    else:                                                                   # 쿠키, 캐시, 세션 파일들의 경로 지정
        filenames = getRemoveDataNames(None, None)

    for filename in filenames:
        if(os.path.exists(srcPath + filename) and os.path.isfile(srcPath + filename)):          # 원본 경로에 파일 존재할 경우
            os.remove(srcPath + filename)                                                       # 파일 삭제

        elif(os.path.exists(srcPath + filename) and os.path.isdir(srcPath + filename)):         # 원본 경로에 폴더 존재할 경우 
            shutil.rmtree(srcPath + filename)                                                   # 폴더 삭제
    
    i = 1                                                   
    while(os.path.exists(multiProfilePath + multiProfilenames[0] + str(i))):        # 멀티프로필 폴더가 존재할 경우
        shutil.rmtree(multiProfilePath + multiProfilenames[0] + str(i))             # 폴더 삭제
        if(os.path.exists(multiProfilePath + multiProfilenames[1])):                # Local State 파일이 존재할 경우
            os.remove(multiProfilePath + multiProfilenames[1])                      # 해당 파일 삭제
        i += 1                                                                      # 모든 멀티 프로필을 삭제하기 위해 순회

# 멀티 프로필 폴더, Local State 파일 경로 반환 메서드 
def getMultiProfilenames():
    multiProfilenames = []
    multiProfilenames.extend(["/Profile ", "/Local State"])         # 다중 프로필 관련 파일들의 경로

    return multiProfilenames

# 6자리 랜덤한 사용자 확인 코드를 생성하기 위한 메서드 
def genCode():
    digits = [i for i in range(0, 10)]                             

    code = ""
    
    for i in range(6):    
        index = math.floor(random.random() * 10)            # 무작위 값 선정
        code += str(digits[index])                          # 선정된 값 이어붙임
    
    return code

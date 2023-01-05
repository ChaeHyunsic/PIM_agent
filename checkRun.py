import psutil


def checkRun():
    check = 0

    for proc in psutil.process_iter():    # 실행중인 프로세스를 순차적으로 검색
        ps_name = proc.name()               # 프로세스 이름을 ps_name에 할당

        if ps_name == "chrome.exe":
            check = 1

    if(check == 0):
        print("None")
    else:
        print("Run")


while(True):
    checkRun()

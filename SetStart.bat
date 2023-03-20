::.bat 기본 세팅 값
    ::모든 명령줄 끄기
    @echo off
    ::UTF8로 설정
    @chcp 65001
    ::모든 명령줄 clean
    cls

goto :CheckUAC

::관리자 권한 취득하기
	:CheckUAC
		@echo off
		::관리자 권한 체크
		>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
		if '%errorlevel%' NEQ '0' (
			goto :UACAccess
		) else ( 
			goto :Done 
		)
		cls
	:UACAccess
		@echo off
		::관리자 권한 주기위해 VBS파일을 생성
		echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
		echo UAC.ShellExecute "cmd", "/c """"%~f0"" """ + Wscript.Arguments.Item(0) + """ ""%user%""""", "%CD%", "runas", 1 >> "%temp%\getadmin.vbs"
		"%temp%\getadmin.vbs" "%file%"

		::관리자 권한 완료후 VBS파일 삭제
		del "%temp%\getadmin.vbs"
		cls
		exit /b
	:Done
		@echo off
		::여기서부터 권리자 권한 필요한 명령어 입력
		copy "%~dp0PIM_AGENT.exe" "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"
		cls
		exit
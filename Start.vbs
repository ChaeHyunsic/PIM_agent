Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "SetStart.bat", "/c lodctr.exe /r" , "", "runas", 0
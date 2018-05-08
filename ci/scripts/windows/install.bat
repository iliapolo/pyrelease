set PATH=%~dp0
set DIR=%PATH:~0,-1%

echo "[install] Starting script"

echo "[install] Installing test dependencies"
%PYTHON%\\python.exe -m pip install -r %DIR%\\..\\..\\..\\test-requirements.txt || goto :error

echo "[install ]Installing dependencies"
%PYTHON%\\python.exe -m pip install -r %DIR%\\..\\..\\..\\requirements.txt || goto :error

echo "[install ]Installing package"
%PYTHON%\\python.exe -m pip install %DIR%\\..\\..\\..\\. || goto :error

dir %PYTHON%\\Scripts

echo "[install] Done!"

exit /b 0

:error
echo [install] Failed with error #%errorlevel%.
exit /b %errorlevel%
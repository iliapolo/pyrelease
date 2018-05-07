set PATH=%~dp0
set DIR=%PATH:~0,-1%

echo "[test] Starting script"

call %DIR%\\install.bat

echo "[test] Running source tests"
%PYTHON%\\python.exe -m pip uninstall -y py-ci || goto :error
%PYTHON%\\python.exe -m pip install %DIR%\\..\\..\\..\\. || goto :error
set PYCI_TEST_PACKAGE=source
%PYTHON%\\Scripts\\py.test.exe -rs --cov-append -c %DIR%\\..\\..\\config\\pytest.ini --cov-config=%DIR%\\..\\..\\config\\coverage.ini --cov=pyci pyci/tests || goto :error

echo "[test] Done!"

exit /b 0

:create_wheel
%PYTHON%\\Scripts\\pyci.exe pack --path %DIR%\\..\\..\\..\\ wheel || goto :error
exit /b 0

:create_binary
%PYTHON%\\Scripts\\pyci.exe pack --path %DIR%\\..\\..\\..\\ binary || goto :error
exit /b 0

:error
echo [test] Failed with error #%errorlevel%.
exit /b %errorlevel%

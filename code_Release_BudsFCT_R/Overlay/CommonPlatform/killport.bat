@echo off

for /l %%p in (6100,1,6105) do (
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p') do (
        echo Found PID: %%i on port %%p
        taskkill /PID %%i /F
    )
)

for /l %%p in (6650,1,6651) do (
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :%%p') do (
        echo Found PID: %%i on port %%p
        taskkill /PID %%i /F
    )
)
@REM pause
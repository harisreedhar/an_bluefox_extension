:: Please run this file in the 'x64 Native Tools Command Prompt for VS 2017'
:: If you don't have it, install Visual Studio 2017
@echo off
setlocal

:: -c      Create only .obj file
:: /EHsc   Set appropriate error handling
:: /GL-    Disable whole program optimization
:: /Ox     Enable full optimization
set args=-c /EHsc /GL- /Ox
cl simplexnoise1234.c %args%
lib *.obj /OUT:Simplex1234_windows.lib

@echo Done.

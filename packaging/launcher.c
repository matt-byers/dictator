#include <Python.h>
#include <mach-o/dyld.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char executable[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) != 0) {
        fprintf(stderr, "Whisper Dictate: executable path is too long\n");
        return 1;
    }

    char resolved[PATH_MAX];
    if (realpath(executable, resolved) == NULL) {
        perror("Whisper Dictate: realpath");
        return 1;
    }

    char resources[PATH_MAX];
    snprintf(resources, sizeof(resources), "%s", resolved);
    char *marker = strstr(resources, "/Contents/MacOS/");
    if (marker == NULL) {
        fprintf(stderr, "Whisper Dictate: launcher is not inside an application bundle\n");
        return 1;
    }
    *marker = '\0';
    strncat(resources, "/Contents/Resources", sizeof(resources) - strlen(resources) - 1);

    char python_path[PATH_MAX * 2];
    snprintf(python_path, sizeof(python_path), "%s/python:%s/site-packages", resources, resources);
    setenv("PYTHONPATH", python_path, 1);
    setenv("PYTHONDONTWRITEBYTECODE", "1", 1);

    Py_Initialize();
    int result = PyRun_SimpleString(
        "from whisper_dictate.main import main\n"
        "raise SystemExit(main())\n"
    );
    Py_Finalize();
    return result == 0 ? 0 : 1;
}

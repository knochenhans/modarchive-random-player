import ctypes
import sys
import warnings

from PySide6.QtWidgets import QApplication

from main_window import MainWindow

from libopenmpt_loader import libopenmpt


def libopenmpt_example_print_error(
    func_name: ctypes.c_char, mod_err: int, mod_err_str: ctypes.c_char | None
):
    if not func_name:
        func_name = ctypes.c_char(b"unknown function")

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            mod_err_str = None
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)
            mod_err_str = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

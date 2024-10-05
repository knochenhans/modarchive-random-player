import ctypes
import warnings

import pyaudio
from PySide6.QtCore import QThread, Signal
from PySide6.QtCore import QCoreApplication

from libopenmpt_loader import error_callback, libopenmpt, log_callback
import logging


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


class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length

    def __init__(self, module_data, module_size, parent=None):
        super().__init__(parent)
        self.module_data = module_data
        self.module_size = module_size
        self.stop_flag = False
        self.pause_flag = False
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("PlayerThread initialized with module size: %d", module_size)

    def run(self):
        SAMPLERATE = 48000
        BUFFERSIZE = 1024
        buffer = (ctypes.c_int16 * (BUFFERSIZE * 2))()

        openmpt_log_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        openmpt_error_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        load_mod = libopenmpt.openmpt_module_create_from_memory2

        ctls = ctypes.c_void_p()
        error = ctypes.c_int()
        error_message = ctypes.c_char_p()

        self.logger.debug("Loading module")
        mod = load_mod(
            self.module_data,  # const void * filedata
            self.module_size,  # size_t filesize
            openmpt_log_func(log_callback),  # openmpt_log_func logfunc
            None,  # void * loguser
            openmpt_error_func(error_callback),  # openmpt_error_func errfunc
            None,  # void * erruser
            ctypes.byref(error),  # int * error
            ctypes.byref(error_message),  # const char ** error_message
            ctls,  # const openmpt_module_initial_ctl * ctls
        )

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=SAMPLERATE,
            output=True,
            frames_per_buffer=BUFFERSIZE,
        )

        module_length = libopenmpt.openmpt_module_get_duration_seconds(mod)
        self.logger.debug("Module length: %f seconds", module_length)


        while not self.stop_flag:
            if self.pause_flag:
                self.logger.debug("Playback paused")
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            libopenmpt.openmpt_module_error_clear(mod)
            count = libopenmpt.openmpt_module_read_interleaved_stereo(
                mod, SAMPLERATE, BUFFERSIZE, buffer
            )
            mod_err = libopenmpt.openmpt_module_error_get_last(mod)
            mod_err_str = libopenmpt.openmpt_module_error_get_last_message(mod)
            if mod_err != libopenmpt.OPENMPT_ERROR_OK:
                self.logger.error("Error reading module: %s", mod_err_str)
                libopenmpt_example_print_error(
                    ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
                    mod_err,
                    mod_err_str,
                )
                libopenmpt.openmpt_free_string(mod_err_str)
                mod_err_str = None
            if count == 0:
                self.logger.debug("End of module reached")
                break
            stream.write(bytes(buffer))

            # Emit position changed signal
            current_position = libopenmpt.openmpt_module_get_position_seconds(mod)
            self.position_changed.emit(int(current_position), int(module_length))

        stream.stop_stream()
        stream.close()
        p.terminate()

        self.logger.debug("Playback stopped")

    def stop(self):
        self.logger.debug("Stop signal received")
        self.stop_flag = True

    def pause(self):
        self.pause_flag = not self.pause_flag
        self.logger.debug("Pause toggled: %s", self.pause_flag)

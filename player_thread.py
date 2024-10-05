import ctypes
from PySide6.QtCore import QThread, Signal
import pyaudio

from libopenmpt_loader import libopenmpt, log_callback, error_callback

class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length

    def __init__(self, module_data, module_size, parent=None):
        super().__init__(parent)
        self.module_data = module_data
        self.module_size = module_size
        self.stop_flag = False
        self.pause_flag = False

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

        while not self.stop_flag:
            if self.pause_flag:
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            libopenmpt.openmpt_module_error_clear(mod)
            count = libopenmpt.openmpt_module_read_interleaved_stereo(
                mod, SAMPLERATE, BUFFERSIZE, buffer
            )
            mod_err = libopenmpt.openmpt_module_error_get_last(mod)
            mod_err_str = libopenmpt.openmpt_module_error_get_last_message(mod)
            if mod_err != libopenmpt.OPENMPT_ERROR_OK:
                libopenmpt_example_print_error(
                    ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
                    mod_err,
                    mod_err_str,
                )
                libopenmpt.openmpt_free_string(mod_err_str)
                mod_err_str = None
            if count == 0:
                break
            stream.write(bytes(buffer))

            # Emit position changed signal
            current_position = libopenmpt.openmpt_module_get_position_seconds(mod)
            self.position_changed.emit(int(current_position), int(module_length))

        stream.stop_stream()
        stream.close()
        p.terminate()

    def stop(self):
        self.stop_flag = True

    def pause(self):
        self.pause_flag = not self.pause_flag

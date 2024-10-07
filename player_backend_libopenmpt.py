import ctypes
import warnings
from typing import Optional

import debugpy
from loguru import logger

from libopenmpt_loader import error_callback, libopenmpt, log_callback
from player_backend import PlayerBackend


def libopenmpt_example_print_error(
    func_name: Optional[ctypes.c_char],
    mod_err: int,
    mod_err_str: Optional[ctypes.c_char],
) -> None:
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


class PlayerBackendLibOpenMPT(PlayerBackend):
    def __init__(self, module_data: bytes, module_size: int) -> None:
        super().__init__(module_data, module_size)
        logger.debug(
            "PlayerBackendLibOpenMPT initialized with module size: {}", module_size
        )

    def load_module(self) -> bool:
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

        logger.debug("Loading module")
        self.mod = load_mod(
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

        if not self.mod:
            logger.error("Failed to load module: {}", error_message.value)
            libopenmpt_example_print_error(
                ctypes.c_char(b"openmpt_module_create_from_memory2()"),
                error.value,
                ctypes.cast(error_message, ctypes.POINTER(ctypes.c_char)).contents,
            )
            libopenmpt.openmpt_free_string(error_message)
            return False

        self.module_metadata = self.get_module_metadata()

        return True

    def get_module_length(self) -> float:
        return libopenmpt.openmpt_module_get_duration_seconds(self.mod)

    def read_interleaved_stereo(
        self, samplerate: int, buffersize: int, buffer: ctypes.Array
    ) -> int:
        libopenmpt.openmpt_module_error_clear(self.mod)
        count = libopenmpt.openmpt_module_read_interleaved_stereo(
            self.mod, samplerate, buffersize, buffer
        )
        mod_err = libopenmpt.openmpt_module_error_get_last(self.mod)
        mod_err_str = libopenmpt.openmpt_module_error_get_last_message(self.mod)
        if mod_err != libopenmpt.OPENMPT_ERROR_OK:
            logger.error("Error reading module: {}", mod_err_str)
            libopenmpt_example_print_error(
                ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
                mod_err,
                mod_err_str,
            )
            libopenmpt.openmpt_free_string(mod_err_str)
        return count

    def get_position_seconds(self) -> float:
        return libopenmpt.openmpt_module_get_position_seconds(self.mod)

    def get_module_title(self) -> Optional[str]:
        return libopenmpt.openmpt_module_get_metadata(self.mod, b"title")

    def get_module_metadata(self) -> dict[str, str]:
        keys = (
            libopenmpt.openmpt_module_get_metadata_keys(self.mod)
            .decode("utf-8")
            .split(";")
        )
        module_metadata = {}
        for key in keys:
            key_c_char_p = ctypes.c_char_p(key.encode('utf-8'))
            value = libopenmpt.openmpt_module_get_metadata(self.mod, key_c_char_p).decode("utf-8")
            if value:
                module_metadata[key] = value
        return module_metadata

    def free_module(self) -> None:
        if self.mod:
            libopenmpt.openmpt_module_destroy(self.mod)
            self.mod = None

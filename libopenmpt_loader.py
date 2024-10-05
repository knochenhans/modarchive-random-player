import sys


if len(sys.argv) > 1:
    libopenmpt_path = sys.argv[1]
else:
    raise ValueError(
        "Please provide the path to libopenmpt_py as a command-line argument."
    )

sys.path.append(libopenmpt_path)

from libopenmpt_py import libopenmpt

def log_callback(user_data, level, message):
    pass


def error_callback(user_data, message):
    pass
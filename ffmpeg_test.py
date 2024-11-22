import ffmpeg
import numpy as np
import sys

def decode_audio(in_filename, **input_kwargs):
    try:
        out = (ffmpeg
            .input(in_filename, **input_kwargs)
            .filter('asetpts', 'PTS-STARTPTS')
            .output('pipe:', format='f32le', acodec='pcm_f32le', ac=1, ar='48k')
            .global_args('-y', '-loglevel', 'panic')
            .overwrite_output()
            .run_async(pipe_stdout=True)
        )
        while True:
            in_bytes = out.stdout.read(4*48000)
            if not in_bytes:
                break
            if len(in_bytes) == 4*48000:
                in_frame = (
                    np
                    .frombuffer(in_bytes, np.float32)
                    .reshape([-1, 48000, 1])
                )
                print(in_frame)  # Process the audio frame here
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    return out

if __name__ == '__main__':
    audio_path = '/mnt/Daten/Musik/Retro/Blood/song-01.mp3'
    decode_audio(audio_path)
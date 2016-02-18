import pylibpd
from sdl2 import SDL_Init, SDL_INIT_AUDIO, SDL_GetError, SDL_Quit
from sdl2 import SDL_AudioSpec, SDL_AudioCallback, AUDIO_S16MSB
from sdl2 import SDL_OpenAudioDevice, SDL_CloseAudioDevice, SDL_PauseAudioDevice
from pdgen import RenderVisitor
import tempfile
import os.path


def get_tempfile(patch):
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.pd')
    visitor = RenderVisitor(tmpfile)
    patch.accept(visitor)
    tmpfile.flush()
    return tmpfile


def audition(patch, out_channels=2, sample_rate=44100):
    pylibpd.libpd_init_audio(1, out_channels, sample_rate)

    if SDL_Init(SDL_INIT_AUDIO) != 0:
        raise RuntimeError("Cannot initialize audio system: {}".format(SDL_GetError()))

    outfile = get_tempfile(patch)

    input(outfile.name)

    pylibpd.libpd_add_to_search_path('/usr/lib/pd/extra/pan')
    pylibpd.libpd_add_to_search_path('/usr/lib/pd/extra/freeverb~')
    pylibpd.libpd_add_to_search_path('/usr/lib/pd/extra/motex')

    patch_file = outfile.name
    #patch_file = '/home/d/code/projects/2d_game/sdl_game/data/pd_patches/simple.pd'
    
    pylibpd.libpd_open_patch(os.path.basename(patch_file),
                             os.path.dirname(patch_file))


    spec = SDL_AudioSpec(0, AUDIO_S16MSB, 0, 0)
    spec.freq = sample_rate
    spec.channels = out_channels
    spec.samples = 2048
    
    ticks_per_block = spec.samples // pylibpd.libpd_blocksize()

    print("Ticks: %u" % (ticks_per_block,))

    def play_audio(notused, stream, size):
        total_runs = int((size / 2) / spec.samples)
        num_samples = pylibpd.libpd_blocksize() * out_channels * ticks_per_block

        for run in range(total_runs):
            outb = bytearray(num_samples * 4)
            inb = bytearray(num_samples * 4)
            pylibpd.libpd_process_float(ticks_per_block, inb, outb)

            for i in range(0, num_samples, 2):
                left = int(outb[i] * 32767)
                #print(left)
                right = int(outb[i + 1] * 32767)
                #print(right)
                stream[i] = left
                stream[i + 1] = right

    spec.callback = SDL_AudioCallback(play_audio)
    devid = SDL_OpenAudioDevice(None, 0, spec, None, 0)
    if devid == 0:
        raise RuntimeError("Unable to open audio device: {}".format(SDL_GetError()))

    SDL_PauseAudioDevice(devid, 0)
    input("Press enter to continue")

    SDL_PauseAudioDevice(devid, 1)
    SDL_CloseAudioDevice(devid)

    pylibpd.libpd_release()
    SDL_Quit(SDL_INIT_AUDIO)

    outfile.close()

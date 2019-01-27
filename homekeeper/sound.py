from math import sin, cos, pi
import pygame
import numpy as np


# pygame.mixer is initted by default with freq 22050, 16 bit ampl, stereo

duration = 3

base_freq = 22050

period = 1 / base_freq

#  mono audio:

base = 432
target = base * 2

envelope = 1
ampl = 32767 // 2

def create_sound(duration, base, target, distort_offset, envelope):
    samples = int(base_freq * duration)
    sample_data = np.zeros((samples, 2), dtype="int16")
    for i in range(samples):
        freq = base + (target - base) * i / samples
        t0 = pi * i * period
        sample_data[i, :] = ampl * sin(freq * t0) * sin((freq - distort_offset) * t0) * sin(envelope * t0)


    #convert to sound object
    return pygame.sndarray.make_sound(sample_data)



def synthesize_sounds():
    sounds = {}
    sounds["level_up"] = create_sound(duration=1, base=432, target=1000, distort_offset=0, envelope=1)
    sounds["vanish"] = create_sound(duration=.3, base=1000, target=700, distort_offset=60, envelope=100)
    sounds["swype"] = create_sound(duration=.03, base=800, target=600, distort_offset=150, envelope=100)

    return sounds


if __name__ == "__main__":
    pygame.init()
    snd = create_sound(duration=.03, base=800, target=600, distort_offset=150, envelope=100)
    snd.play()

    pygame.time.delay(int(duration * 300) + 200)

    pygame.quit()

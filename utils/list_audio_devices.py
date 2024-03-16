import pygame.mixer
import pyaudio

pygame.mixer.init()

devices = pygame.mixer.get_num_channels()

print(f"Number of devices: {devices}")

audio = pyaudio.PyAudio()
num_devices = audio.get_device_count()

for i in range(num_devices):
    device_info = audio.get_device_info_by_index(i)
    print(device_info)
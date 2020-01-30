import windows_volume

if __name__ == '__main__':
    audio = windows_volume.WindowsAudio()
    audio.set_all_to_master()
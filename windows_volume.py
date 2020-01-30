# https://github.com/AndreMiras/pycaw
# https://docs.microsoft.com/en-us/windows-hardware/drivers/audio/default-audio-volume-settings
# https://docs.microsoft.com/en-us/windows/desktop/CoreAudio/audio-tapered-volume-controls

'''
zero seems to be:
20 * math.log10(1/65535)
which is -96.329...

100% seems to be:
20 * math.log10(65535/65535)
which is 0

This gets the value from the slider.
GetMasterVolumeLevelScalar() 
'''

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
#from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw import pycaw

import psutil
import win32gui
import win32process


class WindowsAudio():
    def __init__(self):
        self.devices = pycaw.AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(
            pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(pycaw.IAudioEndpointVolume))

    @property
    def mute(self):
        return bool(self.volume.GetMute())

    @mute.setter
    def mute(self, state):
        if not isinstance(state, bool):
            raise ValueError
        self.volume.SetMute(state, None)

    @property
    def master_volume(self):
        '''Master volume slider value.'''
        return round(self.volume.GetMasterVolumeLevelScalar(), 2)

    @master_volume.setter
    def master_volume(self, value):
        '''Set master volume using slider value.'''
        value = float(value)
        if not 0.0 <= value <= 1:
            raise ValueError('master volume value not between 0.0 and 1.0')
        self.volume.SetMasterVolumeLevelScalar(value, None)

    @property
    def master_decibels(self):
        return self.volume.GetMasterVolumeLevel()

    @master_decibels.setter
    def master_decibels(self, value):
        '''This can be set from -96 (0%) to 0 (100%). See notes. -10.5 is 50%'''
        self.volume.SetMasterVolumeLevel(value, None)

    def master_volume_range(self):
        return self.volume.GetVolumeRange()

    @property
    def sessions(self):
        return pycaw.AudioUtilities.GetAllSessions()
    
    def set_all_to_master(self):
        # TODO: This master volume isn't related to the app.
        #       Just set it or figure out where the current volume really is.
        for session in self.sessions:
            volume = session._ctl.QueryInterface(pycaw.ISimpleAudioVolume)
            starting_volume = volume.GetMasterVolume()
            print(starting_volume)
            if starting_volume != 1.0 or True:
                # Set individual application volume to 100% of master volume.
                volume.SetMasterVolume(1, None)
                ending_volume = volume.GetMasterVolume()
                #print('set {} volume from {} to {}'.format('app', starting_volume, ending_volume))
                print('set PID {} volume from {} to {}'.format(session.ProcessId, starting_volume, ending_volume))


def all_apps_to_master_volume():
    '''Set individual application volume to 100% of master volume.'''
    sessions = pycaw.AudioUtilities.GetAllSessions()
    for session in sessions:
        print(dir(session))
        volume = session._ctl.QueryInterface(pycaw.ISimpleAudioVolume)
        volume.SetMasterVolume(1, None)
        #starting_volume = volume.GetMasterVolume()
        #if starting_volume != 1.0:
        #    # Set individual application volume to 100% of master volume.
        #    volume.SetMasterVolume(1, None)
        #    ending_volume = volume.GetMasterVolume()
        #    print('set {} volume from {} to {}'.format('app', starting_volume, ending_volume))


# use the psutil ppid to get the parent pid, then put into this function.
def get_hwnds(pid):
    """return a list of window handlers based on it process id"""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds 

# This will get the description (friendly name) of an exe.
def getFileDescription(windows_exe):
    try:
        language, codepage = win32api.GetFileVersionInfo(windows_exe, '\\VarFileInfo\\Translation')[0]
        stringFileInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (language, codepage, "FileDescription")
        description = win32api.GetFileVersionInfo(windows_exe, stringFileInfo)
    except:
        description = "unknown"

    return description

def get_session_process_names(sessions):
    '''Build a list of tuples containing process names and descriptions.'''
    names = []
    for session in sessions:
        if session.Process:
            try:
                exe_description = getFileDescription(session.Process.exe())
                print(exe_description)
                names.append((session.Process.name(), exe_description))
            except psutil.AccessDenied:
                print('denied for', session.Process)
                names.append((session.Process.name(), None))
        else:
            print('no process')
            names.append((None, None))
    return names
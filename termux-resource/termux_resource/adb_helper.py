import subprocess

def run_adb_shell(command):
    """
    Runs a command on the device via adb shell.
    """
    return subprocess.run(['adb', 'shell', command], capture_output=True, text=True)

def run_adb_shell_su(command):
    """
    Runs a command on the device via adb shell with root privileges.
    """
    return subprocess.run(['adb', 'shell', 'su', '-c', command], capture_output=True, text=True)

def adb_pull(remote_path, local_path):
    """
    Pulls a file from the device.
    """
    return subprocess.run(['adb', 'pull', remote_path, local_path], capture_output=True, text=True)

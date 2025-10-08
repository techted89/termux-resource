#!/bin/sh
#
# This script launches rish (the Shizuku shell) with access to the Termux
# environment, including the $PATH and shared libraries.
#
# This allows you to use Termux commands within the rish shell, which runs
# with the elevated permissions granted by Shizuku.

# 1. Set the Termux environment prefix.
#    This is the root directory for the Termux installation.
PREFIX="/data/data/com.termux/files/usr"

# 2. Prepend the Termux binary directory to the PATH.
#    This ensures that the shell looks for commands in Termux's bin folder first.
#    We also include standard system paths to ensure basic commands are available.
export PATH="$PREFIX/bin:$PREFIX/bin/applets:$PATH"

# 3. Prepend the Termux library directory to the LD_LIBRARY_PATH.
#    This tells the dynamic linker where to find shared libraries (.so files)
#    that Termux packages depend on.
export LD_LIBRARY_PATH="$PREFIX/lib:$LD_LIBRARY_PATH"

# 4. Set the HOME directory to the Termux home.
#    This makes sure that programs running inside rish use the correct
#    home directory for configuration files.
export HOME="/data/data/com.termux/files/home"

# 5. Execute rish, passing all script arguments to it.
#    The `exec` command replaces the current shell process with rish, so when
#    you exit rish, the script terminates.
exec rish "$@"
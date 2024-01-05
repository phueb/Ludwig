#!/usr/bin/env bash

# note: hebb is turned off. lecun cannot be accessed because password based authentication is off and the authorized keys file in ~/.ssh/authorized_keys needs to be updated.

for hostname in bengio hawkins hinton hoff norman pitts;
do

    echo ${hostname}:

    # this is supposed to forward the password to the sudo command
    # note: this only works after adding `ph ALL=(ALL) NOPASSWD: /usr/bin/python3.7` to the sudoers file using `sudo visudo`
     ssh ${hostname} "sudo python3.7 -m pip install -U pip"

    # this is for updating to the latest version
#    ssh ${hostname} "python3.7 -m pip install -U torch"

    # this is for updating to a specific version
#    ssh ${hostname} "python3.7 -m pip install torch==X.X.X"

    # this is for installing a package from GitHub
#    ssh ${hostname} "python3.7 -m pip install https://github.com/UIUCLearningLanguageLab/AOCHILDES/archive/v2.1.0.tar.gz"

    # update pip (but this works only because the flag --user avoids a permission error.
    # but this only applies changes to the user ph, which means the changes won't affect the user ludwig.
#    ssh ${hostname} "python3.7 -m pip install --user -U pip"

    # this updates non-Python packages (like GPU drivers)
    # ssh ${hostname} "sudo apt-get install nvidia-418 -y "

echo
done

# use --yes flag to skip confirmation when uninstalling via pip
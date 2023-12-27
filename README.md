Android Remote GPT
by Jonathan Germain
Copyright 2023
Released under the GNU GPL Version 3

# Introduction

AndroidRemoteGPT is an android frontend for chatbots running on remote servers. It is an Android/Termux miniapp that provides a convenient way to access a chatbot or other inference engine running on a remote server via ssh. It is targeted towards users of open source generative AI models such as those provided via gpt4all.

# Installation

AndroidRemoteGPT requires both Android and Termux. It also requires Termux:GUI. Because of an [ongoing problem with signing of the F-droid Termux:GUI package](https://github.com/termux/termux-gui/issues/4), you must use the [github Termux release](https://github.com/termux/termux-app/releases) rather than the F-droid Termux release. Versions of Termux from Google Play should never be used as they are insecure and will not be patched. 

This software is built for a client/server model. It requires a server on which inference takes place. As of December 2023, there are a variety of open source models and architectures available that can be run on linux. Instructions will be provided for [gpt4all](https://gpt4all.io/index.html), but the frontend can be used with many different backends.

## Installation on the Android device

1. If Termux or Termux:API has been installed from F-droid or Google Play, remove them completely. The presence of any Termux app installed from a non-Github source will block installation from Github.
2. Download and install [Termux from Github](https://github.com/termux/termux-app/releases). This app was tested with Termux 118.
3. Download and install [Termux:GUI from Github](https://github.com/termux/termux-gui/releases). This app was tested with Termux:GUI 0.16
4. Launch Termux and let it configure itself.
5. In Termux, run "pkg update". If this fails, run "termux-change-repo" and try again.
6. In Termux, run "pkg install openssh"
7. In Termux, run "pkg install python3"
8. In Termux, run "pip install termuxgui"
9. Copy AndroidRemoteGPT.py from wherever you have saved it to the Termux home directory
10. Copy ".androidGPT" to the Termux home directory
11. In Termux, run "mkdir .ssh; chmod 700 .ssh"
12. Create an ssh key and [set up key-based authentication with your ssh server](https://tecadmin.net/setup-key-based-ssh-login/)
13. Set up the [SSH config file](https://phoenixnap.com/kb/ssh-config). For example, the file in .ssh/config might contain
```
host yourserver
user aiuser
hostname yourserver.com
identityfile ~/.ssh/id
```
14. ssh into the server to make sure that it works and get the host key.

Installation is complete. Now, you can run "python AndroidRemoteGPT.py"


## Example of ssh server setup for gpt4all

1. As root, create a new user named aiuser. Also create a home directory for this user and ensure that the user has ownership of this directory.
```
useradd aiuser
mkdir /home/aiuser
chown aiuser.aiuser /home/aiuser
```
2. Ensure that python is installed. On Ubuntu, run "apt -y install python3"
3. Do the server portion of [key-based authentication setup](https://tecadmin.net/setup-key-based-ssh-login/).
4. Place "*" in the password portion of the /etc/shadow entry for aiuser
5. su to aiuser run "su aiuser"
6. Install gpt4all. We start by installing gpt4all via pip to install any dependencies, but the version in pip is old, so we remove it and compile/install the latest version.
```
pip install gpt4all
pip uninstall gpt4all
pip install typer

git clone --recurse-submodules https://github.com/nomic-ai/gpt4all

cd gpt4all/gpt4all-backend/
mkdir build
cd build
cmake ..
cmake --build . --config Release
cd ~/gpt4all/gpt4all-bindings/python/
pip install -e .
```
7. Download your models. Models can be downloaded from [gpt4all.io](https://gpt4all.io/index.html).
8. Link your models to where gpt4all can find them. 
```
mkdir ~/.cache
mkdir ~/.cache/gpt4all
cd ~/.cache/gpt4all
ln -s /where/you/store/your/models/* .
```
9. The console interface for gpt4all is ~/gpt4all/gpt4all-bindings/cli/app.py
10. Create a shell script to run your model
```
#!/bin/sh
python3 ~/gpt4all/gpt4all-bindings/cli/app.py repl --model /wherever/you/put/your/model.gguf
```
Optionally, you may include "-t (# of threads)" and "-d gpu" or "-d nvidia" if you have a video card that you wish to use.

11. Test the shell script
12. Optional: Prepend the public key entry in ~/.ssh/authorized_keys with `command="/home/aiuser/your_script.sh",restrict to limit use of the ai inference user account

# Usage

First, access the configuration page and ensure that your server information is correct. The next command indicator (NCI) and startup sequence are particularly important. The startup sequence is a list of shell commands to run on the server in order to reach the inference interface. The NCI tells the frontend when the chatbot has finished its answer. For gpt4all version 1.0.2, the NCI is the single character "⇢"

Then, go back to the main page and click "connect".

The intro screen should appear. You can then enter your query in the box at the top of the screen and click request to send the query. Note that you must click "request"; pressing enter alone will not send the query.

# Questions

1. Why rely on Termux? Why not use one of the various SSH libraries available for Android and make this a standalone app?

Secure communication is complex. Openssh is one of the most heavily tested programs in the field; I fear that any less heavily tested ssh implementation will introduce security-related bugs that I don't have the bandwidth to manage.

2. Can I use this with systems other than gpt4all?

Yes. If you are pulling models from huggingface and writing your own python scripts to run inference or you use models other than chatbots, this will work. Just be sure to change the next command indicator when you change systems.

# Plans

1. Pretty up the interface
2. Add an icon so that AndroidRemoteGPT can be launched from Android directly without first loading Termux
3. Add text-to-speech
4. Add an on-device inference option for people who have 8gb of RAM on their android devices
5. Allow ssh passwords?
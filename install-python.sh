#!/usr/bin/env bash

apt-get install vim coreutils less

git clone https://github.com/pyenv/pyenv.git ~/.pyenv

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'export PYENV_VERSION=3.6.1' >> ~/.bashrc
echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc

source ~/.bashrc

pyenv install 3.6.1
pyenv global 3.6.1

pip install --upgrade pip
pip install hypothesis

wget https://cmake.org/files/v2.8/cmake-2.8.12.1.tar.gz
tar -xf cmake-2.8.12.1.tar.gz
cd cmake-2.8.12.1 && ./bootstrap && make && make install

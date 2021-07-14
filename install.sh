#!/bin/bash
set -e
trap "" SIGINT

[ -z "$LC_ALL" ] && export LC_ALL=C.UTF-8
[ -z "$LANG" ] && export LANG=C.UTF-8

DOWNLOAD_URL=$(curl -fsSL https://api.github.com/repos/ironsource-mobile/gdbt/releases/latest \
        | grep browser_download_url \
        | cut -d '"' -f 4)
WHEEL_DIR=$(mktemp -d 2>/dev/null)
WHEEL_FILE="$WHEEL_DIR/${DOWNLOAD_URL##*/}"
trap "rm -rf $WHEEL_DIR >/dev/null 2>&1 || true && echo \"ERROR: GDBT wasn't installed\" && exit 1" ERR

echo -en "Downloading latest wheel from GitHub..."
curl -fsSL -o $WHEEL_FILE "$DOWNLOAD_URL"
echo -en "done\n"

echo -en "Detecting Python..."
if pyenv versions >/dev/null 2>&1 && [[ $(python -V 2>/dev/null) == *"Python 3"* ]]
then
    echo -en "$(python -V | sed 's/Python //g') (pyenv)\n"
    PIP="$(which pip)"
elif HOMEBREW_PIP=$(brew list python3 -q 2>/dev/null | grep "pip3$")
then
    echo -en "$($HOMEBREW_PIP -V | grep -Eo 'python [0-9.]+' | sed 's/python //g') (homebrew)\n"
    PIP=$HOMEBREW_PIP
elif [[ $(python3 -V 2>/dev/null) == *"Python 3"* ]]
then
    echo -en "$(python3 -V | sed 's/Python //g') (system)\n"
    PIP="$(which pip3)"
    if [ $(id -u 2>/dev/null) != "0" ] && which sudo >/dev/null 2>&1
    then
        PIP="$(which sudo) $PIP"
    fi
else
    echo -en "ERROR: Python 3 not found\n"
    exit 1
fi

echo -en "Installing GDBT..."
$PIP install --upgrade --upgrade-strategy eager -qq "$WHEEL_FILE"
rm -rf $WHEEL_DIR >/dev/null 2>&1 || true
echo -en "done\n"

echo -en "Verifying installation..."
[[ $(gdbt version 2>/dev/null) == *"GDBT version"* ]]
echo -en "ok\n"

trap - EXIT
trap - SIGINT

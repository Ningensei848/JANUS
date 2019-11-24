#!/bin/bash -e

USER_ID=$(id -u)
GROUP_ID=$(id -g)
PASSWD=${PASSWD:-${DEFAULT_PASSWD}}
USER=${USER:-${DEFAULT_USER}}

# グループを作成する
echo "GROUP_ID: $GROUP_ID"
if [ x"$GROUP_ID" != x"0" ]; then
    groupadd -g $GROUP_ID $USER
fi

# ユーザを作成する
echo "USER_ID: $USER_ID"
if [ x"$USER_ID" != x"0" ]; then
    export HOME=/home/$USER
    useradd -d ${HOME} -m -s /bin/bash -u $USER_ID -g $GROUP_ID $USER
fi

# パーミッションを元に戻す
sudo chmod u-s /usr/sbin/useradd
sudo chmod u-s /usr/sbin/groupadd

# ログインユーザ名を設定する
USER=$(whoami)
echo "USER: $USER"

# ログインパスワードを設定する
echo "PASSWD: $PASSWD"
echo ${USER}:${PASSWD} | sudo chpasswd

[ ! -e ${HOME}/.xsession ] && cp /etc/skel/.xsession ${HOME}/.xsession

echo "#############################"

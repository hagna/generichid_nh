#!/bin/sh
set -x


read -p "to: " TO
sendit() {
  subj=$1
  msg=$2
cat <<EOF  | msmtp -C deleteme $TO
From: Nate <natester@gmail.com>
Subject: $subj

$msg
EOF

}

catit() {
  msg=$2
  subj=$1
  cat <<EOF
--------------------
$subj

$msg
EOF
}


read -p "gmail username: " uname
stty -echo
read -p "password: " passw; echo
stty echo

cat <<EOF > deleteme
defaults
auth on
tls on 
tls_trust_file /usr/share/ca-certificates/mozilla/Equifax_Secure_CA.crt
account gmail
host smtp.gmail.com
port 587
from $uname
user $uname
password $passw
account default : gmail
EOF

chmod 0600 deleteme

catit "[RFC generichid v3 1/13]" "$(git diff --stat -p remotes/bluez.git/master...pleasingdave1) "
catit "[RFC generichid v3 2/13]" "$(git diff --stat -p pleasingdave1..pleasingdave2)"
catit "[RFC generichid v3 3/13]" "$(git diff --stat -p pleasingdave2..pleasingdave3)"
catit "[RFC generichid v3 4/13]" "$(git diff --stat -p pleasingdave3..pleasingdave4)"
catit "[RFC generichid v3 5/13]" "$(git diff --stat -p pleasingdave4..pleasingdave5)"
catit "[RFC generichid v3 6/13]" "$(git diff --stat -p pleasingdave5..pleasingdave6)"
catit "[RFC generichid v3 7/13]" "$(git diff --stat -p pleasingdave6..pleasingdave7)"
catit "[RFC generichid v3 8/13]" "$(git diff --stat -p pleasingdave7..pleasingdave8)"
catit "[RFC generichid v3 9/13]" "$(git diff --stat -p pleasingdave8..pleasingdave9)"
catit "[RFC generichid v3 10/13]" "$(git diff --stat -p pleasingdave9..pleasingdave10)"
catit "[RFC generichid v3 11/13]" "$(git diff --stat -p pleasingdave10..pleasingdave11)"
catit "[RFC generichid v3 12/13]" "$(git diff --stat -p pleasingdave11..pleasingdave12)"
catit "[RFC generichid v3 13/13]" "$(git diff --stat -p pleasingdave12..pleasingdave13)"

rm deleteme

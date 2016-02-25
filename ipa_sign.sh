#!/usr/bin/env bash

INSPECT_ONLY=0
if [[ "$1" == '-i' ]]; then
    INSPECT_ONLY=1
    shift
fi

if [[ "$1" == '-l' ]]; then
    security find-certificate -a | awk '/^keychain/ {if(k!=$0){print; k=$0;}} /"labl"<blob>=/{sub(".*<blob>=","          "); print}'
    exit
fi

if [[ ! ( # any of the following are not true
        # 1st arg is an existing regular file
        -f "$1" &&
        # ...and it has a .ipa extension
        "${1##*.}" == "ipa" &&
        # 2nd arg is an existing regular file
        ($INSPECT_ONLY == 1 || -f "$2") &&
        # ...and it has an .mobileprovision extension
        ($INSPECT_ONLY == 1 || "${2##*.}" == "mobileprovision") &&
        # 3rd arg is a non-empty string
        ($INSPECT_ONLY == 1 || -n "$3")
        ) ]];
    then
        cat << EOF >&2
    Usage: $(basename -- "$0") Application.ipa foo/bar.mobileprovision "iPhone Distribution: I can haz code signed"
    Usage: $(basename -- "$0") -i Application.ipa

    Options:
      -i    Only inspect the package. Do not resign it.
      -l    List certificates and exit
EOF
    exit;
fi

## Exit on use of an uninitialized variable
set -o nounset
## Exit if any statement returns a non-true return value (non-zero)
set -o errexit
## Announce commands
#set -o xtrace

realpath(){
    echo "$(cd "$(dirname "$1")"; echo -n "$(pwd)/$(basename -- "$1")")";
}

IPA="$(realpath $1)"
PROVISION="$(realpath "$2")"
TMP="$(mktemp -d /tmp/resign.$(basename -- "$IPA" .ipa).XXXXX)"
IPA_NEW="$(pwd)/$(basename -- "$IPA" .ipa).resigned.ipa"
CLEANUP_TEMP=0 # Do not remove this line or "set -o nounset" will error on checks below
#CLEANUP_TEMP=1 # Uncomment this line if you want this script to clean up after itself
cd "$TMP"
[[ $CLEANUP_TEMP -ne 1 ]] && echo "Using temp dir: $TMP"
unzip -q "$IPA"
plutil -convert xml1 Payload/*.app/Info.plist -o Info.plist
echo "App has BundleDisplayName '$(/usr/libexec/PlistBuddy -c 'Print :CFBundleDisplayName' Info.plist)' and BundleShortVersionString '$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' Info.plist)'"
echo "App has BundleIdentifier  '$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' Info.plist)' and BundleVersion $(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' Info.plist)"
#security cms -D -i Payload/*.app/embedded.mobileprovision > mobileprovision.plist
#echo "App has provision         '$(/usr/libexec/PlistBuddy -c "Print :Name" mobileprovision.plist)', which supports '$(/usr/libexec/PlistBuddy -c "Print :Entitlements:application-identifier" mobileprovision.plist)'"
if [[ ! ($INSPECT_ONLY == 1) ]]; then
    CERTIFICATE="$3"
    security cms -D -i "$PROVISION" > provision.plist
    echo "Embedding provision       '$(/usr/libexec/PlistBuddy -c "Print :Name" provision.plist)', which supports '$(/usr/libexec/PlistBuddy -c "Print :Entitlements:application-identifier" provision.plist)'"
    rm -rf Payload/*.app/_CodeSignature Payload/*.app/CodeResources
    CURRENTDIR=$(pwd)
    cd Payload/*.app/
    cp "$PROVISION" embedded.mobileprovision
    cd $CURRENTDIR
    /usr/bin/codesign -f -s "$CERTIFICATE" Payload/*.app
    zip -qr "$IPA_NEW" Payload
fi
[[ $CLEANUP_TEMP -eq 1 ]] && rm -rf "$TMP"
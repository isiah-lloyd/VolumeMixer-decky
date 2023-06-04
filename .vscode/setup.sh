#!/usr/bin/env bash

if [[ "$CLI_INSTALLED" > "0" ]] || [[ "$CLI_INSTALLED" < "0" ]]; then
    echo "The Decky CLI tool (binary file is just called "decky") is used to build your plugin as a zip file which you can then install on your Steam Deck to perform testing. We highly recommend you install it. Hitting enter now will run the script to install Decky CLI and extract it to a folder called cli in the current plugin directory. You can also type 'no' and hit enter to skip this but keep in mind you will not have a usable plugin without building it."
    read run_cli_script
    if [[ "$run_cli_script" =~ "n" ]]; then
        echo "You have chosen to not install the Decky CLI tool to build your plugins. Please install this tool to build and test your plugin before submitting it to the Plugin Database."
    else
        mkdir $(pwd)/cli
        curl -L -o $(pwd)/cli/decky "https://github.com/SteamDeckHomebrew/cli/releases/download/0.0.1-alpha.11/decky"
        chmod +x $(pwd)/cli/decky
        echo "Decky CLI tool is now installed and you can build plugins into easy zip files using the "Build Zip" Task in vscodium."
    fi
fi
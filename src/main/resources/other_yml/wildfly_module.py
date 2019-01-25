#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import json

"""
Ansible module to manage wildfly modules (war,jar,ear, etc.)
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
- name: Deploy module
  wildfly_module:
       name: 'murex.all.signed.trades.resend.test'
       version: '1.1'
       extension: 'war'
       # present/absent/redeploy
	   state: 'present' 
       # path to folder without last slash
	   sourcepath: '/tmp/deployments' 
       serverAddress: 'localhost:9990'
       cli_sh: '/opt/wildfly-12.0.0.Final/bin/jboss-cli.sh'  
'''

CLI_COMMAND = "{0} --output-json --connect --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --output-json --connect --controller={1} --commands='{2}'"

def handle_result(rc,out,module):
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string

def parse_json_out(out):
    out = out.replace("=>", ":")
    j_content = json.loads("[" + out + "]")
    return j_content[0]     

def get_installed_modules(module, client_sh, address):    

    cmd = CLI_COMMAND.format(client_sh, address,"/deployment=*:read-attribute(name=name)")
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
    
    installedModules=set() 
    
    parsed_out = parse_json_out(out)
    
    if (parsed_out["outcome"]=="success"):
        result = parsed_out["result"]               
    
    for module_info in result:
        installedModules.add(module_info["result"])
    
    return installedModules, cmd, out, err, rc

    
def install_module(client_sh, address, module, war_name,path_to_war):    

    module_install_command = "deploy {0}/{1} --force".format(path_to_war,war_name)
    cmd = CLI_COMMAND.format(client_sh, address,module_install_command)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
       
    return out, err, rc

def uninstall_module(client_sh, address, module, war_name):    

    module_install_command = "undeploy {0}".format(war_name)
    cmd = CLI_COMMAND.format(client_sh, address,module_install_command)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
       
    return out, err, rc
    
def main():
    module = AnsibleModule(
        argument_spec=dict(
            serverAddress=dict(required=True),
            name=dict(required=True),
            version=dict(required=True),
            extension=dict(default="war"),
            state=dict(default="present"),
            sourcepath=dict(required=True),
            cli_sh=dict(required=True)
        )
    )
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
    
    cmd = ""
    out = ""
    err = ""
    rc  = ""
    installedModules, cmd, out, err, rc = get_installed_modules(module, cli_sh,serverAddress)    
    
    changed = False
    
    wf_module_name = "{0}-{1}.{2}".format(module.params["name"],module.params["version"],module.params["extension"])
    
    if (not (wf_module_name in installedModules) and (module.params["state"]=="present")) or (module.params["state"]=="redeploy"):
        out, err, rc = install_module(cli_sh, serverAddress, module, wf_module_name, module.params["sourcepath"])
        changed = True
    elif (wf_module_name in installedModules) and (module.params["state"]=="absent"):
        out, err, rc = uninstall_module(cli_sh, serverAddress, module, wf_module_name)
        changed = True
        
    module.exit_json(changed=changed, out=out, err=err, rc=rc, mods=installedModules)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

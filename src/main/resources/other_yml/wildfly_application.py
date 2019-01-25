#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
from xml.etree import ElementTree as ET
import os
import json
import re

"""
Ansible module to manage wildfly modules (war,jar,ear, etc.)
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
- name: Deploy applications
    wildfly_application:
       applications: '{{wf_instance.wildfly_applications}}'
       sourcepath: '{{wf_instance.binary_path}}'
       configchangeinfo: '{{config_change_result}}'
       serverAddress: '{{controller}}'
       moduletypes: 'jar,rar' # Optional (default value is 'war,ear') - types of artifacts to install
       operations: 'install,uninstall,redeploy' # Optional (default value is 'install,uninstall,redeploy') - what we need to do in this step
       cli_sh: '{{wf_instance.cli_sh}}'  

...
wildfly_applications: 
     - group_id: "ru.sberbank.cib.gmbus"
       artifact_id: "availability-check-service"
       extension: "war"
       version: "1.7"
       config: "availability.check.service.yml"
       state: present
     - group_id: "ru.sberbank.cib.gmbus"
       artifact_id: "audit-data-storage-api"
       extension: "war"
       version: "1.18"       
       runtime_name: "audit-data-storage-api" # WITHOUT .war extension!
       state: present
       '''

CLI_COMMAND = "{0} --output-json --connect --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --output-json --connect --controller={1} --commands='{2}'"
DEFAULT_DEPLOYMENT_ORDER = 5

def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string

def parse_json_out(out):
    out = out.replace("=>", ":").replace("undefined","\"undefined\"")
    j_content = json.loads("[" + out + "]")
    return j_content[0]     

def get_deployment_name(module):
    return "{0}-{1}.{2}".format(module["artifact_id"],module["version"],module["extension"])

def get_installed_modules(ansible, client_sh, address,targetExtensions):    

    cmd = CLI_COMMAND.format(client_sh, address,"/deployment=*:read-attribute(name=name)")
    rc, out, err = ansible.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        ansible.fail_json(msg=reason)
    
    installedModules=set() 
    
    parsed_out = parse_json_out(out)
    
    if (parsed_out["outcome"]=="success"):
        result = parsed_out["result"]               
    
    for module_info in result:
        modulename, module_extension = os.path.splitext(module_info["result"])
        if module_extension[1:] in targetExtensions:
            installedModules.add(module_info["result"])
    
    return installedModules

# Строит карту зависимостей для каждого модуля - список тех модулей, что его использует
def get_dependency_map(ansible, client_sh, address,modules):
    
    dep_map = dict()
    for module in modules:    
        read_dep_sctuc_command = "attachment display --operation=/deployment={0}:read-content(path=META-INF/jboss-deployment-structure.xml)".format(module)    
        cmd = CLI_COMMAND.format(client_sh, address,read_dep_sctuc_command)
        rc, out, err = ansible.run_command(cmd)
        
        if rc !=0 :
          continue
        
        # Удаляем первую строку с технической информацией, оставляем чистый xml
        out = re.sub(r"^ATTACHMENT (.)+", "", out)       
            
        dep_structure = ET.fromstring(out)        
        
        for e in dep_structure.findall('.//dependencies/module'):           
            depend_name = re.sub(r"^deployment.", "", e.get('name'))
            if e.get('name') in dep_map.keys():                
                dep_map[depend_name].append(module)
            else:
                dep_map[depend_name]=[module]
        
    return dep_map

def install_module(client_sh, address, ansible, war_name, runtime_name ,path_to_war):    

    module_install_command = "deploy {0}/{1} --runtime-name={2}.war --force".format(path_to_war,war_name,runtime_name)
    cmd = CLI_COMMAND.format(client_sh, address,module_install_command)
    rc, out, err = ansible.run_command(cmd)
        
    reason = ""
    if rc != 0:
        reason = parse_error(out)        
       
    return rc,reason

def uninstall_module(client_sh, address, ansible, module_to_uninstall, dep_map, modulesNeedToUninstall, modules_already_uninstalled):    
    
    if not module_to_uninstall in modulesNeedToUninstall:
        return 10, "Cannot remove module {0} because of it is not marked for uninstalling".format(module_to_uninstall)
    elif module_to_uninstall in modules_already_uninstalled:
        return 0,"Already deleted"
    
    if module_to_uninstall in dep_map.keys():
        for dependant_module in dep_map[module_to_uninstall]:
            if dependant_module == module_to_uninstall:
                return 10, "Cannot remove module {0} because of recursive dependency of itself".format(module_to_uninstall)  
            if not (module_to_uninstall in modules_already_uninstalled):
                rc,reason = uninstall_module(client_sh, address, ansible, dependant_module, dep_map, modulesNeedToUninstall,modules_already_uninstalled)
            if rc !=0:
                return rc, "Cannot remove module {0} because of -> {1}".format(module_to_uninstall,reason)  
                    
    module_remove_command = "undeploy {0}".format(module_to_uninstall)
    cmd = CLI_COMMAND.format(client_sh, address,module_remove_command)
    rc, out, err = ansible.run_command(cmd)
        
    reason = ""
    if rc != 0:
        reason = parse_error(out)        
    else:
        modules_already_uninstalled.add(module_to_uninstall)
    
    return rc, reason
    
def reload_module(client_sh, address, ansible, war_name):    

    module_redeploy_command = "cd deployment={0},:undeploy,:deploy".format(war_name)
    
    cmd = CLI_COMMANDS.format(client_sh, address,module_redeploy_command)
    
    rc, out, err = ansible.run_command(cmd)
            
    reason = ""
    if rc != 0:
        reason = parse_error(out)       
           
    return rc, reason
    
def disable_module(client_sh, address, ansible, war_name):    

    module_disable_command = "cd deployment={0},:undeploy".format(war_name)
    
    cmd = CLI_COMMANDS.format(client_sh, address,module_disable_command)
    
    rc, out, err = ansible.run_command(cmd)
            
    reason = ""
    if rc != 0:
        reason = parse_error(out)       
           
    return rc, reason

def enable_module(client_sh, address, ansible, war_name):    

    module_enable_command = "cd deployment={0},:deploy".format(war_name)
    
    cmd = CLI_COMMANDS.format(client_sh, address,module_enable_command)
    
    rc, out, err = ansible.run_command(cmd)
            
    reason = ""
    if rc != 0:
        reason = parse_error(out)       
           
    return rc, reason

def find_module_by_deployment_name(module_full_name,all_modules):    
    result = filter(lambda module: module['deployment_name'] == module_full_name, all_modules)    
    if len(result)>0:
        return result[0]
    else:
        return dict()
    
def extend_modules_list_by_deployment_name(modules_list):
    for module in modules_list:
        module["deployment_name"]=get_deployment_name(module)
        if not "runtime_name" in module.keys():
            module["runtime_name"] = module["deployment_name"]

def sort_by_deployment_order(modules_list):
    return sorted(modules_list,key=lambda k: k['order'] if 'order' in k.keys() else DEFAULT_DEPLOYMENT_ORDER)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            serverAddress=dict(required=True),
            applications=dict(required=False,type="list",default=[]),
            configchangeinfo=dict(required=False,type="dict",default={}),            
            sourcepath=dict(required=True),
            moduletypes=dict(default="war,ear"),
            operations=dict(default="install,uninstall,redeploy"), 
            cli_sh=dict(required=True)
        )
    )
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
    targetExtensions = set(module.params["moduletypes"].split(","))
    operations = module.params["operations"].split(",")
    
    # Add full deployment name to module structure
    extend_modules_list_by_deployment_name(module.params["applications"])
        
    # Check configuration correctness + (if needed) change 'order' attribute type (for correct futher sorting)
    for app in module.params["applications"]:
        if not app["extension"] in targetExtensions:
            module.fail_json(msg="Incorrect inclution of module {0}.{1} in {2}-type operation".format(app["artifact_id"],app["extension"],module.params["moduletypes"]))
        elif ("order" in app.keys()) and (type(app["order"]) is str):
            app["order"] = int(app["order"])
    
    addedModules = set()
    removedModules = set()
    redeployedModules = set()
    failedModules = list()
    
    changed = False    
    
    installedModules = get_installed_modules(module, cli_sh,serverAddress,targetExtensions)        
    actualModulesInConfig=set([app["deployment_name"] for app in module.params["applications"] if app["state"]=="present"])
    
    modulesNeedToInstall = [find_module_by_deployment_name(m,module.params["applications"]) for m in (actualModulesInConfig - installedModules)]
    modulesNeedToInstall = sort_by_deployment_order(modulesNeedToInstall)        
    modulesNeedToUninstall = installedModules - actualModulesInConfig          
    modulesPossibleNeedToRefresh = installedModules & actualModulesInConfig    
   
    dep_map = get_dependency_map(module, cli_sh, serverAddress,modulesNeedToUninstall)
    
    already_uninstalled_modules = set()
    if "uninstall" in operations:
        for wf_module in modulesNeedToUninstall:                
            if not (wf_module in already_uninstalled_modules):
                rc,reason = uninstall_module(cli_sh, serverAddress, module, wf_module,dep_map,modulesNeedToUninstall,already_uninstalled_modules)
                if rc==0:
                    removedModules = removedModules|already_uninstalled_modules
                    changed = True
                else:
                    failedModules.append({wf_module:reason})

    if "install" in operations:
        for wf_module in modulesNeedToInstall:        
            rc,reason = install_module(cli_sh, serverAddress, module, wf_module["deployment_name"],wf_module["runtime_name"],module.params["sourcepath"])
            if rc==0:
                addedModules.add(wf_module["deployment_name"])
                changed = True
            else:
                failedModules.append({wf_module["deployment_name"]:reason})
    
    if "redeploy" in operations:
        for wf_module_name in modulesPossibleNeedToRefresh:
            module_attributes = find_module_by_deployment_name(wf_module_name,module.params["applications"])
            if not module_attributes:
                failedModules.append({wf_module_name:"Cannot find module {0} in config modules list".format(wf_module_name)})           
                continue
            configChangeResult = module.params["configchangeinfo"]
            if len(configChangeResult) > 0 and configChangeResult["changed"] == True:
                configCopyResults = configChangeResult["results"]
                for configCopyResult in configCopyResults:
                    if (configCopyResult["item"]["artifact_id"] == module_attributes["artifact_id"]) \
                    and (configCopyResult["item"]["version"] == module_attributes["version"]) \
                    and (configCopyResult["item"]["extension"] == module_attributes["extension"]) \
                    and (configCopyResult["changed"] == True):
                        changed = reload_module(cli_sh, serverAddress, module, wf_module_name)
                        if changed:
                            redeployedModules.add(wf_module_name)
    
    # На последующих шагах из каталога конфигурационных файлов будут удалены все файлы, кроме указанных тут
    config_files_retention_list = [app["config"] for app in module.params["applications"] if ((app["state"]=="present") and ("config" in app.keys()))]
    
    module.exit_json(changed=changed, addedModules=addedModules, removedModules=removedModules, redeployedModules=redeployedModules, failedModules=failedModules, config_files_retention_list=config_files_retention_list)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

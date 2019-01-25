#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

"""
Ansible module to manage wildfly datasources
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

DOCUMENTATION = '''
---
module: wildfly_datasource
short_description: Install, uninstall or change wildfly datasources
description:
    - Install, uninstall or change wildfly datasource options
options:
    name:
        description:
            - symbolic name of the datasource
        required: true
        default: null
    jndiName:
        description:
            - JNDI name of the datasource
        required: true
        default: null
    connectionUrl:
        description:
            - JDBC URL of the specified datasource
        required: true
        default: null
    driverName:
        description:
            - Name of JDBC driver used for connection
        required: true
        default: null
    userName:
        description:
            - User name for DB connection
        required: true
        default: null
    password:
        description:
            - Password for DB connection
        required: true
        default: null
    state:
        description:
            - Required state of the datasource. (present/absent)
        required: false
        default: present
    serverAddress:
        description:
            - hostname/IP addres of the target wildfly instance
        required: true
        default: null
    cli_sh:
        description:
            - The full path of the jboss-cli.sh utility
        required: false
        default: /opt/wildfly-12.0.0.Final/bin/jboss-cli.sh
    
'''

EXAMPLES = '''
# Datasource definition task:
- name: Install datasources
   wildfly_datasource: 
      name: '{{item.name}}'
      jndiName: '{{item.jndiName}}'
      connectionUrl: '{{item.connectionUrl}}'
      driverName: '{{item.driverName}}'
      userName: '{{item.userName}}'
      password: '{{item.password}}'
      state: '{{item.state}}'
      serverAddress: '{{item.serverAddress}}'
      cli_sh: '{{item.cli_sh}}'
   with_items:
        - '{{datasources}}'

'''

DS_STATE_MAP = dict(
    present="createOrUpdate",
    absent="delete"
)

CLI_COMMAND = "{0} --connect --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --connect --controller={1} --commands='{2}'"

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
        
def wasChanged(module, client_sh, address, datasource):
    """ Checks if given datasource parameters diffe from current configuration.

    :param module: ansible module proxy
    :param client_sh: wildfly cli command bin
    :param datasource: new datasource configuration
    :return: True is current datasource configuration on the server differs from given config params
    """

    getExistingParamsCommand = CLI_COMMANDS.format(client_sh, address,"cd subsystem=datasources/data-source={0},ls".format(datasource["name"]))
    rc, out, err = module.run_command(getExistingParamsCommand)

    lines = out.split('\n')
    fixCommandTemplate = '/subsystem=datasources/data-source={0}:write-attribute(name={1},value="{2}"),'
    fixCommand = ''
    wasChanged = False
    
    for line in lines:
       if '=' in line:
          keyValue = line.split('=',1)          
          if ((keyValue[0] in datasource.keys()) and (str(datasource[keyValue[0]])!=keyValue[1].strip())):
            wasChanged = True
            fixCommand = fixCommand + fixCommandTemplate.format(datasource["name"],keyValue[0],datasource[keyValue[0]])            
          elif ((keyValue[0] in datasource["properties"].keys()) and (str(datasource["properties"][keyValue[0]])!=keyValue[1].strip())):
            wasChanged = True
            fixCommand = fixCommand + fixCommandTemplate.format(datasource["name"],keyValue[0],datasource["properties"][keyValue[0]])            
            
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
    
    return wasChanged, fixCommand[:-1]

def get_installed_datasources(module, client_sh, address):
    """ Get all available datasources from the specified server.

    :param module: ansible module proxy
    :param client_sh: wildfly cli command bin
    :param address: wildfly server address in host:port format    
    :return: List of available datasources
    """

    cmd = CLI_COMMANDS.format(client_sh, address,"cd subsystem=datasources/data-source,ls")
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
    
    installedDataSources=[]
    
    out = out.strip()
    
    installedDataSources = out.split()    
    
    return installedDataSources, cmd, out, err, rc

def install_new_datasource(module, client_sh, address, ds_params):
    """ Install new datasource.

    :param module: ansible module proxy
    :param client_sh: wildfly cli command bin
    :param address: wildfly server address in host:port format    
    :param ds_params: datasourcedefinition parameters
    :return: create datasource command, reason code
    """

    createDatasourceCommand = "data-source add --jndi-name='{0}' --name='{1}' --connection-url='{2}' --driver-name='{3}' --user-name='{4}' --password='{5}'"
    createDatasourceCommand = createDatasourceCommand.format(ds_params["jndi-name"],ds_params["name"],ds_params["connection-url"],ds_params["driver-name"],ds_params["user-name"],ds_params["password"])
    
    cmd = CLI_COMMANDS.format(client_sh, address,createDatasourceCommand)
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module)
    
    setupDataSourceCommandTemplate = "/subsystem=datasources/data-source={0}:write-attribute(name={1}, value='{2}')"         
    setPropertiesCommand = ""
    if ds_params["properties"]:
        for name,value in ds_params["properties"].iteritems():
            setPropertiesCommand = setPropertiesCommand + setupDataSourceCommandTemplate.format(ds_params["name"],name,value) + ","    
    
    cmd = CLI_COMMANDS.format(client_sh, address,setPropertiesCommand[:-1])        
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module)
    
    return cmd, out, err, rc

def remove_datasource(module, client_sh, address, ds_name):
    """ Removes datasource.

    :param module: ansible module proxy
    :param client_sh: wildfly cli command bin
    :param address: wildfly server address in host:port format    
    :param ds_name: datasource name to delete
    :return: remove datasource command, reason code, messages
    """

    removeDatasourceCommand = "data-source remove --name='{0}'"
    removeDatasourceCommand = removeDatasourceCommand.format(ds_name)
    
    cmd = CLI_COMMANDS.format(client_sh, address,removeDatasourceCommand)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
       
    return cmd, out, err, rc

def change_datasource(module, client_sh, address, changeDatasourceCommand):
    
    cmd = CLI_COMMANDS.format(client_sh, address,changeDatasourceCommand)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
       
    return cmd, out, err, rc
    
def main():
    module = AnsibleModule(
        argument_spec=dict(
            serverAddress=dict(required=True),
            name=dict(required=True),
            jndiName=dict(required=True),
            connectionUrl=dict(required=True),
            driverName=dict(required=True),
            properties=dict(required=False,type="dict",default={}),            
            userName=dict(required=True),
            password=dict(required=True),
            state=dict(default="present", choices=DS_STATE_MAP.keys()),
            cli_sh=dict(required=True)
        )
    )
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
    
    ds_params = {
                     "name":module.params["name"],
                     "jndi-name":module.params["jndiName"],
                     "connection-url":module.params["connectionUrl"],
                     "driver-name":module.params["driverName"],                     
                     "properties":module.params["properties"],
                     "user-name":module.params["userName"],
                     "password":module.params["password"],
                     "state":module.params["state"]                  
                     }
    
    cmd = ""
    out = ""
    err = ""
    rc  = ""
    installedDataSources, cmd, out, err, rc = get_installed_datasources(module, cli_sh,serverAddress)    
    
    changed = False    
    
    if (not ds_params["name"] in installedDataSources) and (ds_params["state"]=="present"):
        cmd, out,err, rc = install_new_datasource(module, cli_sh,serverAddress,ds_params)
        changed = True
    elif (ds_params["name"] in installedDataSources) and (ds_params["state"]=="absent"): 
        cmd, out,err, rc = remove_datasource(module,cli_sh,serverAddress,ds_params["name"])
        changed = True 
    elif (ds_params["name"] in installedDataSources) and (ds_params["state"]=="present"): 
        dsWasChanged,fixCommand = wasChanged(module,cli_sh,serverAddress,ds_params)
        if dsWasChanged:            
            change_datasource(module,cli_sh,serverAddress,fixCommand)
            changed = True
      
    module.exit_json(changed=changed, datasource=ds_params["name"])

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

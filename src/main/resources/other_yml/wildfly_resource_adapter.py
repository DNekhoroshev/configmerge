#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *

"""
Ansible module to manage wildfly resource adapters
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
# RA definition task:
- name: Install resource_adapters - {{wf_instance.servicename}}
        wildfly_resource_adapter: 
          id: '{{item.id}}'
          archive: '{{item.archive}}'
          transactionSupport: '{{item.transactionSupport}}'
          connectionDefinitions: '{{item.connectionDefinitions}}'
          configProperties: '{{item.configProperties|default(omit)}}'
          adminObjects: '{{item.adminObjects|default(omit)}}'       
          state: '{{item.state}}'
          cli_sh: '{{wf_instance.cli_sh}}'
          serverAddress: '{{controller}}'
        when: item.archive is defined
        with_items:
            - '{{wf_instance.resource_adapters}}'

# RA properties definition:
resource_adapters:
 - archive: 'wmq.jmsra.rar'
   transactionSupport: 'NoTransaction'
   #possible values: present/absent
   state: present
   cli_sh: '/opt/wildfly-12.0.0.Final/bin/jboss-cli.sh'
   serverAddress: '{{inventory_hostname}}:9990'
   connectionDefinitions:
     - name: "cfName"
       className: "com.ibm.mq.connector.outbound.ManagedConnectionFactoryImpl"
       jndiName: "java:jboss/jms/ivt/JMS2CF"
       pool:
         name: "JMS2CF"
         minSize: "10"
         maxSize: "25"
         initSize: "15"
       properties:
         channel: "SYSTEM.DEF.SVRCONN"
         hostName: "gmbus-mq-dev-01"
         transportType: "CLIENT"
         queueManager: "ExampleQM"
         port: "1414"
   adminObjects:
     - name: "aoName"
       className: "com.ibm.mq.connector.outbound.MQQueueProxy"
       jndiName: "java:jboss/jms/ivt/IVTQueue"
       poolName: "IVTQueue"
       properties:
         baseQueueName: "TEST.QUEUE"                
'''

RA_STATE_MAP = dict(
    present="createOrUpdate",
    absent="delete",    
)

CLI_COMMAND = "{0} --connect --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --connect --controller={1} --commands='{2}'"

def get_installed_rars(module, client_sh, address):    

    cmd = CLI_COMMANDS.format(client_sh, address,"cd /subsystem=resource-adapters/resource-adapter=,ls")
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
    
    installedRars=[]
    
    out = out.strip()
    
    installedRars = out.split()    
    
    return installedRars, out, err, rc  
    
def get_actual_connection_definitions(ra_params_cds):
    actualCDs=set()
    for cd in ra_params_cds:
        actualCDs.add(cd["pool"]["name"])
    
    return actualCDs
    
def get_actual_admin_objects(ra_params_aos):
    actualAOs=set()
    for ao in ra_params_aos:
        actualAOs.add(ao["name"])
    
    return actualAOs
    
def get_installed_rar_connection_definitions(module, client_sh, address, ra_name):    

    cmd = CLI_COMMANDS.format(client_sh, address,"cd /subsystem=resource-adapters/resource-adapter={0}/connection-definitions,ls".format(ra_name))
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
    
    installedCDs=[]
    
    out = out.strip()    
    installedCDs = out.split()     
       
    return set(installedCDs)

def get_installed_rar_admin_objects(module, client_sh, address, ra_name):    

    cmd = CLI_COMMANDS.format(client_sh, address,"cd /subsystem=resource-adapters/resource-adapter={0}/admin-objects,ls".format(ra_name))
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)
    
    installedAOs=[]
    
    out = out.strip()    
    installedAOs = out.split()     
       
    return set(installedAOs)

def addConnDefToRA(module, client_sh, address, ra_name,conn_def):
    createRarCDCommand = "/subsystem=resource-adapters/resource-adapter={0}/connection-definitions={1}:add(\
    class-name={2}, \
    jndi-name={3}, \
    enabled={4}, \
    use-java-context={5}, \
    initial-pool-size={6}, \
    min-pool-size={7}, \
    max-pool-size={8}, \
    )".format(ra_name,conn_def["pool"]["name"],\
    conn_def["className"],\
    conn_def["jndiName"],\
    "true",\
    "true",\
    conn_def["pool"]["initSize"],\
    conn_def["pool"]["minSize"],\
    conn_def["pool"]["maxSize"]\
    )
    
    cmd = CLI_COMMANDS.format(client_sh, address,createRarCDCommand)
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module,cmd)           
    
    for cd_property_key,cd_property_value in conn_def["properties"].iteritems():
        createRarCDPropCommand = "/subsystem=resource-adapters/resource-adapter={0}/connection-definitions={1}/config-properties={2}/:add(value='{3}')"\
        .format(ra_name,conn_def["pool"]["name"],cd_property_key,cd_property_value)
        cmd = CLI_COMMANDS.format(client_sh, address,createRarCDPropCommand)
        rc, out, err = module.run_command(cmd)
        handle_result(rc,out,module,cmd)   

def addAdminObjectToRA(module, client_sh, address, ra_name,admin_object):
    createRarAOCommand = "/subsystem=resource-adapters/resource-adapter={0}/admin-objects={1}:add(class-name={2},jndi-name='{3}')".format(ra_name,admin_object["name"],admin_object["className"],admin_object["jndiName"])
    
    cmd = CLI_COMMANDS.format(client_sh, address,createRarAOCommand)
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module,cmd)
    
    for ao_property_key,ao_property_value in admin_object["properties"].iteritems():
        createRarAOPropCommand = "/subsystem=resource-adapters/resource-adapter={0}/admin-objects={1}/config-properties={2}/:add(value='{3}')"\
        .format(ra_name,admin_object["name"],ao_property_key,ao_property_value)
        cmd = CLI_COMMANDS.format(client_sh, address,createRarAOPropCommand)
        rc, out, err = module.run_command(cmd)
        handle_result(rc,out,module,cmd)
        
def removeConnDefinitionsFromRA(module, client_sh, address, ra_name,conn_def_names):
    
    for conn_def_name in conn_def_names:
        removeRarCDCommand = "/subsystem=resource-adapters/resource-adapter={0}/connection-definitions={1}:remove".format(ra_name,conn_def_name)
        cmd = CLI_COMMANDS.format(client_sh, address,removeRarCDCommand)
        rc, out, err = module.run_command(cmd)
        handle_result(rc,out,module,cmd)

def removeAdminObjectsFromRA(module, client_sh, address, ra_name,admin_object_names):
    
    for ao_name in admin_object_names:
        removeRarAOCommand = "/subsystem=resource-adapters/resource-adapter={0}/admin-objects={1}:remove".format(ra_name,ao_name)
        cmd = CLI_COMMANDS.format(client_sh, address,removeRarAOCommand)
        rc, out, err = module.run_command(cmd)
        handle_result(rc,out,module,cmd)        
    
def install_new_rar(module, client_sh, address, ra_params):    

    createRarCommand = "/subsystem=resource-adapters/resource-adapter={0}:add(archive={1}, transaction-support={2})".format(ra_params["id"], ra_params["archive"],ra_params["transactionSupport"])
    cmd = CLI_COMMANDS.format(client_sh, address,createRarCommand)
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module,cmd)
    
    for cd in ra_params["connectionDefinitions"]:        
        addConnDefToRA(module, client_sh,address, ra_params["id"],cd)   
    
    for config_property_key,config_property_value in ra_params["configProperties"].iteritems():
        createRarConfigPropCommand = '/subsystem=resource-adapters/resource-adapter={0}/config-properties={1}:add(value="{2}")'\
        .format(ra_params["id"],config_property_key,config_property_value)        
        cmd = CLI_COMMANDS.format(client_sh, address,createRarConfigPropCommand)
        rc, out, err = module.run_command(cmd)
        handle_result(rc,out,module,cmd)   
    
    if "adminObjects" in ra_params:
        for ao in ra_params["adminObjects"]:
            createAdmObjectCommand = "/subsystem=resource-adapters/resource-adapter={0}/admin-objects={1}:add(class-name={2}, jndi-name={3})"\
            .format(ra_params["id"],ao["name"],ao["className"],ao["jndiName"])
            cmd = CLI_COMMANDS.format(client_sh, address,createAdmObjectCommand)
            rc, out, err = module.run_command(cmd)
            handle_result(rc,out,module,cmd)
        
            if "properties" in ao:
                for ao_property_key,ao_property_value in ao["properties"].iteritems():
                    createRarAOPropCommand = "/subsystem=resource-adapters/resource-adapter={0}/admin-objects={1}/config-properties={2}/:add(value='{3}')"\
                    .format(ra_params["id"],ao["name"],ao_property_key,ao_property_value)
                    cmd = CLI_COMMANDS.format(client_sh, address,createRarAOPropCommand)
                    rc, out, err = module.run_command(cmd)
                    handle_result(rc,out,module,cmd)       
    
    return cmd, out, err, rc
    
def delete_rar(module, client_sh, address, ra_name):
    deleteRarCommand = "/subsystem=resource-adapters/resource-adapter={0}:remove".format(ra_name)
    cmd = CLI_COMMANDS.format(client_sh, address,deleteRarCommand)
    rc, out, err = module.run_command(cmd)
    handle_result(rc,out,module,cmd)
    
    return cmd, out, err, rc
    
def handle_result(rc,out,module,command):
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason+", failed command: {0}".format(command))
        
def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(required=True),
            archive=dict(required=True),
            transactionSupport=dict(default="NoTransaction"),
            connectionDefinitions=dict(required=True,type="list"),
            adminObjects=dict(required=False,type="list",default=[]),
            configProperties=dict(required=False,type="dict",default={}),
            state=dict(default="present", choices=RA_STATE_MAP.keys()),
            serverAddress=dict(required=True),
            cli_sh=dict(required=True)
        )
    )
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
    
    ra_params = {
                     "id":module.params["id"],
                     "archive":module.params["archive"],
                     "transactionSupport":module.params["transactionSupport"],
                     "connectionDefinitions":module.params["connectionDefinitions"],
                     "adminObjects":module.params["adminObjects"],
                     "configProperties":module.params["configProperties"],
                     "state":module.params["state"]
                     }
    
    cmd = ""
    out = ""
    err = ""
    rc  = 0
    
    changed = False
        
    for conDef in ra_params["connectionDefinitions"]:
        if not ("properties" in conDef):
            conDef["properties"] = {}
        
    installedRars, out, err, rc = get_installed_rars(module, cli_sh,serverAddress) 
    
    if (not ra_params["id"] in installedRars) and (ra_params["state"]=="present"):
        cmd, out,err, rc = install_new_rar(module, cli_sh,serverAddress,ra_params)
        changed = True
    elif (ra_params["id"] in installedRars) and (ra_params["state"]=="absent"):
        cmd, out,err, rc = delete_rar(module, cli_sh,serverAddress,ra_params["id"])
        changed = True    
    elif (ra_params["id"] in installedRars) and (ra_params["state"]=="present"):        
        presentCDs = get_installed_rar_connection_definitions(module, cli_sh,serverAddress,ra_params["id"])        
        actualCDs = get_actual_connection_definitions(ra_params["connectionDefinitions"])        
        CDNeedToInstall = actualCDs - presentCDs
        CDNeedToRemove = presentCDs - actualCDs        
        
        for conDef in ra_params["connectionDefinitions"]:
           if (conDef["pool"]["name"] in CDNeedToInstall):
              addConnDefToRA(module, cli_sh,serverAddress, ra_params["id"],conDef)
              changed = True
           
        if (len(CDNeedToRemove)>0):
            removeConnDefinitionsFromRA(module, cli_sh,serverAddress, ra_params["id"],CDNeedToRemove)
            changed = True
        
        presentAOs = get_installed_rar_admin_objects(module, cli_sh,serverAddress,ra_params["id"])
        actualAOs = get_actual_admin_objects(ra_params["adminObjects"])
        AONeedToInstall = actualAOs - presentAOs
        AONeedToRemove = presentAOs - actualAOs
        
        for adminObject in ra_params["adminObjects"]:
           if (adminObject["name"] in AONeedToInstall):
              addAdminObjectToRA(module, cli_sh,serverAddress, ra_params["id"],adminObject)
              changed = True
           
        if (len(AONeedToRemove)>0):
            removeAdminObjectsFromRA(module, cli_sh,serverAddress, ra_params["id"],AONeedToRemove)
            changed = True
        
    module.exit_json(changed=changed, state=ra_params["state"], out=out, err=err, rc=rc)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()
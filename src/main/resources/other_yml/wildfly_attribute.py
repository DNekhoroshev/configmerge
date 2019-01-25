#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import json

"""
Ansible module to manage wildfly configuration attributes
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
- name: Undertow setup for LDAP on Wildfly instance '{{controller}}'
  wildfly_attribute:    
     path: '/subsystem=undertow/server=default-server/https-listener=https'
     attr_name: 'security-realm' 
     attr_value: 'LDAPWSSecurityRealm'
     serverAddress: '{{controller}}'
     cli_sh: '{{wf_instance.cli_sh}}'

- name: Security domain setup for LDAP on Wildfly instance '{{controller}}'
  wildfly_attribute:
     batch:
        - path: '/subsystem=security/security-domain=other/authentication=classic/login-module=RealmDirect'
          attr_name: 'module-options.realm' 
          attr_value: 'LDAPWSSecurityRealm'    
        - path: '/subsystem=undertow/server=default-server/https-listener=https'
          attr_name: 'security-realm' 
          attr_value: 'ApplicationRealm'
     serverAddress: '{{controller}}'
     cli_sh: '{{wf_instance.cli_sh}}'               
'''

CLI_COMMAND = "{0} --connect --output-json --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --connect --output-json --controller={1} --commands='{2}'"

def parse_json_out(module, out):        
    out = out.replace("=>", ":").replace("undefined","\"undefined\"")    
    try:
        j_content = json.loads("[" + out + "]")
        return j_content[0]
    except:
        module.fail_json(msg="Error parsing out: "+out) 

def getWriteAttrCommand(attrDefinition):
    return "{0}:write-attribute(name={1}, value={2})".format(attrDefinition["path"],attrDefinition["attr_name"],attrDefinition["attr_value"])
    
def getUndefineAttrCommand(attrDefinition):
    return "{0}:undefine-attribute(name={1})".format(attrDefinition["path"],attrDefinition["attr_name"])
    
def executeBatch(module, cli_sh,serverAddress,batch):    

    batchCommand = 'batch,'
    batchCount = 0
    for attrDefinition in batch:        
        if not "attr_state" in attrDefinition:
            attrDefinition["attr_state"] = "defined"
            
        if attrDefinition["attr_state"] == "undefined":
            batchCommand = batchCommand+getUndefineAttrCommand(attrDefinition)+','
            batchCount+=1
        else:
            currentAttrValue = read_attr(module, cli_sh,serverAddress,attrDefinition)       
            if currentAttrValue != attrDefinition["attr_value"]:
                batchCommand = batchCommand+getWriteAttrCommand(attrDefinition)+','
                batchCount+=1                       
    rc  = 0
    out = ''
    err = ''
    changed = False
    cmd=''
    
    if batchCount:
        batchCommand = batchCommand+'run-batch'    
        cmd = CLI_COMMANDS.format(cli_sh, serverAddress,batchCommand)        
        rc, out, err = module.run_command(cmd)
        if rc:
            module.fail_json(msg=err,out=out,rc=rc,cmd=cmd)
        changed = True
    
    return changed,cmd
    
def read_attr(module, cli_sh,serverAddress,attr_params):    

    cli_cmd = ":read-attribute(name={0})".format(attr_params["attr_name"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,attr_params["path"]+cli_cmd)
    rc, out, err = module.run_command(cmd)
    
    parsed_out = parse_json_out(module,out)
    
    if rc != 0:
        return ""
        #reason = parse_error(out)
        #module.fail_json(msg=reason)      
    
    return parsed_out['result']
    
def write_attr(module, cli_sh,serverAddress,attr_params):    

    cli_cmd = ":write-attribute(name={0}, value={1})".format(attr_params["attr_name"],attr_params["attr_value"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,attr_params["path"]+cli_cmd)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
    
    parsed_out = parse_json_out(module,out)
    
    if "failure-description" in parsed_out:
        module.fail_json(msg=parsed_out["failure-description"])
            
    return True, cmd
    
def undefine_attr(module, cli_sh,serverAddress,attr_params):    

    cli_cmd = ":undefine-attribute(name={0})".format(attr_params["attr_name"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,attr_params["path"]+cli_cmd)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
    
    parsed_out = parse_json_out(module,out)
    
    if "failure-description" in parsed_out:
        module.fail_json(msg=parsed_out["failure-description"])    
        
    return True, cmd
    
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=False),
            batch=dict(required=False,type='list'),
            attr_name=dict(required=False),
            attr_value=dict(default=""),
            attr_state=dict(default="defined"),            
            serverAddress=dict(required=True),
            cli_sh=dict(required=True)
        )
    )
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
    
    attrDefList = list()
    
    batchMode = False             
    changed = False
    cmd = ""
    
    if module.params["batch"]:
        attrDefList = module.params["batch"]
        batchMode = True
    else: 
        attrDefList = [{
                     "path":module.params["path"],
                     "attr_name":module.params["attr_name"],
                     "attr_value":module.params["attr_value"],
                     "attr_state":module.params["attr_state"]                     
                     }]       
    
    if batchMode:
        changed,cmd = executeBatch(module, cli_sh,serverAddress,attrDefList)
    else:   
        if module.params["attr_state"] == "undefined":
            changed,cmd = undefine_attr(module, cli_sh,serverAddress,attrDefList[0])            
        else:
            currentAttrValue = read_attr(module, cli_sh,serverAddress,attrDefList[0]) 
        
            if currentAttrValue != attrDefList[0]["attr_value"]:
                changed,cmd = write_attr(module, cli_sh,serverAddress,attrDefList[0])                
    
    module.exit_json(changed=changed, cmd=cmd)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

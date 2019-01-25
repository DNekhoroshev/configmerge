from ansible.module_utils.basic import *
import json

"""
Ansible module to manage wildfly configuration objects
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
- name: Setup LDAP security on Wildfly instance '{{controller}}' step 3
  wildfly_object:
      obj_path: '/core-service=management/security-realm=LDAPWSSecurityRealm/authentication=ldap'
      obj_params: 'connection="LDAPConnection", base-dn="CN=Users,DC=msk,DC=trd,DC=ru", username-attribute="cn", recursive=false'
      obj_state: present
      serverAddress: '{{controller}}'
      cli_sh: '{{wf_instance.cli_sh}}'

- name: Setup LDAP security on Wildfly instance '{{controller}}' step 4
  wildfly_object:
      batch:
        - obj_path: '/core-service=management/security-realm=LDAPWSSecurityRealm/authorization=ldap'
          obj_params: 'connection="LDAPConnection"'
          obj_state: present
        - obj_path: '/core-service=management/security-realm=LDAPWSSecurityRealm/authorization=ldap/group-search=principal-to-group'
          obj_params: 'group-name-attribute="cn", group-attribute="memberOf"'
          obj_state: present
      serverAddress: '{{controller}}'
      cli_sh: '{{wf_instance.cli_sh}}'               
'''

CLI_COMMAND = "{0} --connect --output-json --controller={1} --command='{2}'"
CLI_COMMANDS = "{0} --connect --output-json --controller={1} --commands='{2}'"

def parse_json_out(module, out):
    out = out.replace("=>", ":").replace("undefined","\"undefined\"").replace("null","\"null\"")    
    try:
        j_content = json.loads("[" + out + "]")
        return j_content[0]
    except:
        module.fail_json(msg="Error parsing out: "+out)

def getDeleteCommand(objectDefinition):
    return "{0}:remove".format(objectDefinition["obj_path"])
    
def getCreateCommand(objectDefinition):
    cmd = ""
    if objectDefinition["obj_params"]:
        cmd = "{0}:add({1})".format(objectDefinition["obj_path"],objectDefinition["obj_params"])
    else:
        cmd = "{0}:add()".format(objectDefinition["obj_path"])
    
    return cmd
    
def executeBatch(module, cli_sh,serverAddress,batch):    

    batchCommand = 'batch,'
    batchCount = 0
    for objectDefinition in batch:
        batchObjectExists = check_object_exists(module, cli_sh,serverAddress,objectDefinition) 
        if batchObjectExists and objectDefinition["obj_state"]=="absent":
            batchCommand = batchCommand+getDeleteCommand(objectDefinition)+','
            batchCount+=1
        elif (not batchObjectExists) and (objectDefinition["obj_state"]=="present"):
            batchCommand = batchCommand+getCreateCommand(objectDefinition)+','      
            batchCount+=1
        elif batchObjectExists and objectDefinition["obj_state"]=="present":
            if get_changed_properties(module, cli_sh,serverAddress,objectDefinition):
                batchCommand = batchCommand+getDeleteCommand(objectDefinition)+','+getCreateCommand(objectDefinition)+','               
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
    
def get_changed_properties(module, cli_sh,serverAddress,obj_params):    

    if not obj_params["obj_params"]:
        return []
    
    cli_cmd = "{0}:read-resource".format(obj_params["obj_path"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,cli_cmd)
    rc, out, err = module.run_command(cmd)        
      
    properties = dict()    
    
    parsed_out = parse_json_out(module, out)
    
    if (parsed_out["outcome"]=="success"):
        result = parsed_out["result"]
    else:
        result = dict()
        
    new_param_list = obj_params["obj_params"].split(",")
    new_param_dict = dict()
    difference = []
    
    for param in new_param_list:
        key_value = param.split("=")
        new_param_dict[key_value[0]]=key_value[1]   
    
    for key,value in new_param_dict.iteritems():
        if (key in result) and (result[key]!=value.translate(None, "'\"")):            
            difference.append(key)
    
    return difference
    
def check_object_exists(module, cli_sh,serverAddress,obj_params):    

    cli_cmd = "cd {0}".format(obj_params["obj_path"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,cli_cmd)
    rc, out, err = module.run_command(cmd)        
      
    if "not found" in out:
        return False
    
    return True

def delete_object(module, cli_sh,serverAddress,obj_params):    

    cli_cmd = "{0}:remove".format(obj_params["obj_path"])
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,cli_cmd)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
    
    parsed_out = parse_json_out(module, out)
    
    if "failure-description" in parsed_out:
        module.fail_json(msg=parsed_out["failure-description"])
    
    return True,cmd

def create_object(module, cli_sh,serverAddress,obj_params):    

    if obj_params["obj_params"]:
        cli_cmd = "{0}:add({1})".format(obj_params["obj_path"],obj_params["obj_params"])
    else:
        cli_cmd = "{0}:add()".format(obj_params["obj_path"])
    
    cmd = CLI_COMMAND.format(cli_sh, serverAddress,cli_cmd)
    rc, out, err = module.run_command(cmd)
        
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)      
    
    parsed_out = parse_json_out(module, out)
    
    if "failure-description" in parsed_out:
        module.fail_json(msg=parsed_out["failure-description"])        
    
    return True,cmd
    
def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def main():
    module = AnsibleModule(
        argument_spec=dict(
            obj_path=dict(required=False),            
            obj_params=dict(required=False),            
            batch=dict(required=False,type='list'),
            obj_state=dict(required=False),
            serverAddress=dict(required=True),
            cli_sh=dict(required=True)
        )
    )
    
    if (not module.params["batch"]) and (not module.params["obj_path"]):
        module.fail_json(msg="You must define one of 'batch'|'obj_path' attributes!")
    
    serverAddress=module.params["serverAddress"]
    cli_sh = module.params["cli_sh"]
        
    objDeflist = list()
    
    batchMode = False             
    changed = False
    cmd = ""
    
    if module.params["batch"]:
        objDeflist = module.params["batch"]
        batchMode = True
    else: 
        objDeflist = [{
                     "obj_path":module.params["obj_path"],
                     "obj_params":module.params["obj_params"],
                     "obj_state":module.params["obj_state"]
                     }]       
    
    if batchMode:
        changed,cmd = executeBatch(module, cli_sh,serverAddress,objDeflist)        
    else:        
        objectExists = check_object_exists(module, cli_sh,serverAddress,objDeflist[0]) 
        
        if objectExists and module.params["obj_state"]=="absent":
           changed,cmd = delete_object(module, cli_sh,serverAddress,objDeflist[0])                            
        elif (not objectExists) and (module.params["obj_state"]=="present"):
           changed,cmd = create_object(module, cli_sh,serverAddress,objDeflist[0])                  
        elif objectExists and module.params["obj_state"]=="present":
           if get_changed_properties(module, cli_sh,serverAddress,objDeflist[0]):               
               changed,cmd = executeBatch(module, cli_sh,serverAddress,objDeflist)             
    
    module.exit_json(changed=changed,cmd=cmd)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

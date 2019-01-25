from ansible.module_utils.basic import *
import pymqi
import os

"""
Ansible module to manage mq subscriptions
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
 - name: Create MQ subscription
   become: yes     
   become_user: mqm
   mq_subscription:
    host: 'ibgm-esb-uat9-d(1414)'
    qmgrName: 'SEG1_GMSB'
    channel: 'DEV.SVRCONN'        
    sub_name: 'sub2'
    topic_name: 'MYTOPIC'    
    # This is addition to topic_string of topic 'MYTOPIC'. Effective topic_string will be something like '/top/mytopic/B'
    topic_string: 'B'
    destination: 'Q3'    
    state: 'present'
'''

def wasChanged(qmgr,sub):    

    pcf = pymqi.PCFExecute(qmgr)

    changedProperties = []
    
    args = {pymqi.CMQCFC.MQCACF_SUB_NAME: sub[pymqi.CMQCFC.MQCACF_SUB_NAME]}
    
    try:
        response = pcf.MQCMD_INQUIRE_SUBSCRIPTION(args)
        for sub_info in response:
            for property in sub.keys():
                if str(sub[property])!=str(sub_info[property]).strip():                    
                    changedProperties.append(property)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_SUBSCRIPTION:            
            raise
    
    return changedProperties

def alter_sub(qmgr,sub,changedProperties):    

    changedProperties.append(pymqi.CMQCFC.MQCACF_SUB_NAME)    
    
    args = {prop : sub[prop] for prop in changedProperties}
    
    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CHANGE_SUBSCRIPTION(sub)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def del_sub(qmgr,sub):    

    pcf = pymqi.PCFExecute(qmgr)

    args = {pymqi.CMQCFC.MQCACF_SUB_NAME : sub[pymqi.CMQCFC.MQCACF_SUB_NAME]}
    
    try:
        pcf.MQCMD_DELETE_SUBSCRIPTION(args)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def create_sub(qmgr,sub):    

    pcf = pymqi.PCFExecute(qmgr)    
        
    try:
        pcf.MQCMD_CREATE_SUBSCRIPTION(sub)
        return True
    except pymqi.MQMIError as e:
        raise e
    

def check_sub_exists(qmgr,subName):    

    args = {pymqi.CMQCFC.MQCACF_SUB_NAME: subName}

    pcf = pymqi.PCFExecute(qmgr)

    try:
        response = pcf.MQCMD_INQUIRE_SUBSCRIPTION(args)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_SUBSCRIPTION:            
            return False
        else:
            qmgr.disconnect()
            raise
    else:    
        return True    

def getSecuredCDSCO(host,channel):
    cd = pymqi.CD()
    cd.ChannelName = channel["name"]
    cd.ConnectionName = host
    cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
    cd.TransportType = pymqi.CMQC.MQXPT_TCP
    cd.SSLCipherSpec = channel["ssl"]["cipher_suite"]
    
    sco = pymqi.SCO()    
    sco.KeyRepository = os.environ['MQCLNTKEYREPODIR']
    
    return cd,sco
    
def main():
    module = AnsibleModule(
        argument_spec=dict(            
            host=dict(required=True),
            qmgrName=dict(required=True),
            channel=dict(required=True,type="dict"),
            sub_name=dict(required=True),
            topic_name=dict(required=True),
            topic_string=dict(default=""),
            destination=dict(required=True),
            selector=dict(default=''),
            state=dict(default="present")            
        )
    )  

    subDef = {
            pymqi.CMQCFC.MQCACF_SUB_NAME : module.params["sub_name"],
            pymqi.CMQC.MQCA_TOPIC_NAME : module.params["topic_name"],
            pymqi.CMQC.MQCA_TOPIC_STRING : module.params["topic_string"],                                    
            pymqi.CMQCFC.MQCACF_DESTINATION : module.params["destination"],
            pymqi.CMQCFC.MQCACF_SUB_SELECTOR : module.params["selector"]
            }
    
    channel = module.params["channel"]
    
    changed = False
    connected = False
    qmgr = pymqi.QueueManager(None)
    
    try:
        if channel['ssl']['enabled'] == 'yes':            
            cd, sco = getSecuredCDSCO(module.params["host"],channel)
            qmgr.connect_with_options(module.params["qmgrName"], cd, sco)
            connected = True
        else:            
            qmgr = pymqi.connect(module.params["qmgrName"], channel["name"], module.params["host"])   
            connected = True
    
        exists = check_sub_exists(qmgr,module.params["sub_name"])      
        
        if not exists and module.params["state"] == 'present':
            create_sub(qmgr,subDef)
            changed = True       
        elif exists and module.params["state"] == 'present' and len(wasChanged(qmgr,subDef))>0:        
            del_sub(qmgr,subDef)
            create_sub(qmgr,subDef)     
            changed = True
        elif exists and module.params["state"] == 'absent':
            del_sub(qmgr,subDef)
            changed = True
    except pymqi.MQMIError as e:
        module.fail_json(msg=str(e),CC=e.comp,RC=e.reason)
    finally:   
        if connected:
            qmgr.disconnect()   
    
    module.exit_json(changed=changed, exists=exists, qmgr=module.params["qmgrName"], sub=module.params["sub_name"])

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()
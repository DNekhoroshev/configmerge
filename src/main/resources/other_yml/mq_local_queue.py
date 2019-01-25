#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import pymqi
import os

"""
Ansible module to manage mq queues
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
 - name: Create MQ local queue
   become: yes     
   become_user: mqm
   mq_local_queue:
    host: 'ibgm-esb-uat9-d(1414)'
    qmgrName: 'SEG1_GMSB'
    name: 'Q3'
    channel: 'DEV.SVRCONN'
    maxDepth: 999
    maxMsgL: 120000 
    persistence: 'no' # default 'yes'
    create_backout: 'yes' # default ''no
    backout_treshold: '10' # default '0'
    state: 'present'
'''

Q_PERSISTENCE_MAP = dict(
    yes = pymqi.CMQC.MQPER_PERSISTENT,
    no  = pymqi.CMQC.MQPER_NOT_PERSISTENT
)

Q_STATE_MAP = dict(
    present = "present",
    absent  = "absent"
)

def wasChanged(qmgr,queue):    

    prefix = queue[pymqi.CMQC.MQCA_Q_NAME]
    queue_type = pymqi.CMQC.MQQT_LOCAL

    args = {pymqi.CMQC.MQCA_Q_NAME: prefix,pymqi.CMQC.MQIA_Q_TYPE: queue_type}

    pcf = pymqi.PCFExecute(qmgr)

    changedProperties = []
    
    try:
        response = pcf.MQCMD_INQUIRE_Q(args)
        for queue_info in response:
            for property in queue.keys():
                if str(queue[property])!=str(queue_info[property]).strip():                    
                    changedProperties.append(property)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
            raise e
       
    return changedProperties

def alter_local_queue(qmgr,queue,changedProperties):    

    changedProperties.append(pymqi.CMQC.MQCA_Q_NAME)
    changedProperties.append(pymqi.CMQC.MQIA_Q_TYPE)
    
    args = {prop : queue[prop] for prop in changedProperties}
    
    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CHANGE_Q(args)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def del_local_queue(qmgr,queue):    

    args = {pymqi.CMQC.MQCA_Q_NAME: queue[pymqi.CMQC.MQCA_Q_NAME],
        pymqi.CMQC.MQIA_Q_TYPE: pymqi.CMQC.MQQT_LOCAL}
    
    pcf = pymqi.PCFExecute(qmgr)
    
    try:
        pcf.MQCMD_DELETE_Q(args)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def create_local_queue(qmgr,queue):        

    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CREATE_Q(queue)        
        return True
    except pymqi.MQMIError as e:
        raise e    

def check_queue_exists(qmgr,queueName):    

    prefix = queueName
    queue_type = pymqi.CMQC.MQQT_LOCAL

    args = {pymqi.CMQC.MQCA_Q_NAME: prefix,pymqi.CMQC.MQIA_Q_TYPE: queue_type}

    pcf = pymqi.PCFExecute(qmgr)

    try:
        response = pcf.MQCMD_INQUIRE_Q(args)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:            
            return False
        else:
            raise e 
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
            name=dict(required=True),
            maxDepth=dict(required=True),
            maxMsgL=dict(required=True),            
            persistence=dict(default="yes", choices=Q_PERSISTENCE_MAP.keys()),            
            create_backout=dict(default="no"),
            backout_treshold=dict(default="0"),
            state=dict(default="present", choices=Q_STATE_MAP.keys())            
        )
    )     
    
    channel = module.params["channel"]
    
    qDef = {
            pymqi.CMQC.MQCA_Q_NAME : module.params["name"],
            pymqi.CMQC.MQIA_Q_TYPE : pymqi.CMQC.MQQT_LOCAL,
            pymqi.CMQC.MQIA_MAX_Q_DEPTH : int(module.params["maxDepth"]),
            pymqi.CMQC.MQIA_MAX_MSG_LENGTH : int(module.params["maxMsgL"]),
            pymqi.CMQC.MQIA_DEF_PERSISTENCE : Q_PERSISTENCE_MAP[module.params["persistence"]],
            pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME : "",
            pymqi.CMQC.MQIA_BACKOUT_THRESHOLD : int(module.params["backout_treshold"])
            }
    
    create_bck = module.params["create_backout"]
    
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
    
        exists = check_queue_exists(qmgr,module.params["name"])    
        backout_exists = check_queue_exists(qmgr,module.params["name"]+".BACK")
    
        if not exists and module.params["state"] == 'present':
            if create_bck=="yes":
                if not backout_exists:
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"] + ".BACK"
                    create_local_queue(qmgr,qDef)
                    qDef[pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME] = qDef[pymqi.CMQC.MQCA_Q_NAME]
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"]
                else:
                    qDef[pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME] = qDef[pymqi.CMQC.MQCA_Q_NAME]+".BACK"         
            
            create_local_queue(qmgr,qDef)            
            changed = True       
        elif exists and module.params["state"] == 'present':        
            if create_bck=="yes":
                if not backout_exists:
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"] + ".BACK"
                    create_local_queue(qmgr,qDef)
                    qDef[pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME] = qDef[pymqi.CMQC.MQCA_Q_NAME]
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"]
                    alter_local_queue(qmgr,qDef,wasChanged(qmgr,qDef))
                    changed = True
                else:
                    qDef[pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME] = module.params["name"]+".BACK"
            elif create_bck=="no":
                qDef[pymqi.CMQC.MQCA_BACKOUT_REQ_Q_NAME] = ""
                if backout_exists:                  
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"] + ".BACK"
                    del_local_queue(qmgr,qDef)
                    qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"]
                    changed = True
            if len(wasChanged(qmgr,qDef))>0:
                alter_local_queue(qmgr,qDef,wasChanged(qmgr,qDef))          
                changed = True
            
        elif exists and module.params["state"] == 'absent':
            del_local_queue(qmgr,qDef)
            if backout_exists:
                qDef[pymqi.CMQC.MQCA_Q_NAME] = module.params["name"] + ".BACK"
                del_local_queue(qmgr,qDef)                
            changed = True
    
    except pymqi.MQMIError as e:
        module.fail_json(msg=str(e),CC=e.comp,RC=e.reason)
    finally:   
        if connected:
            qmgr.disconnect()
    
    module.exit_json(changed=changed, qmgr=module.params["qmgrName"],queue=module.params["name"])

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import pymqi
import os

"""
Ansible module to manage mq topics
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
 - name: Create MQ topic
   become: yes     
   become_user: mqm
   mq_topic:
    host: 'ibgm-esb-uat9-d(1414)'
    qmgrName: 'SEG1_GMSB'
    topic_name: 'TOPICA'
    topic_string: '/top/A/myA'
    publish: 'enabled'
    subscribe: 'enabled'
    durable_sub: 'disabled'
    channel: 'DEV.SVRCONN'        
    state: 'present'
'''

TOPIC_PERSISTENCE_MAP = dict(
    yes = pymqi.CMQC.MQPER_PERSISTENT,
    no  = pymqi.CMQC.MQPER_NOT_PERSISTENT
)

TOPIC_PUB_MAP = dict(
    enabled = pymqi.CMQC.MQTA_PUB_ALLOWED,
    disabled  = pymqi.CMQC.MQTA_PUB_INHIBITED
)

TOPIC_SUB_MAP = dict(
    enabled = pymqi.CMQC.MQTA_SUB_ALLOWED,
    disabled  = pymqi.CMQC.MQTA_SUB_INHIBITED
)

TOPIC_DUR_SUB_MAP = dict(
    enabled = pymqi.CMQC.MQSUB_DURABLE_ALLOWED,
    disabled  = pymqi.CMQC.MQSUB_DURABLE_INHIBITED
)

def wasChanged(qmgr,topic):    

    pcf = pymqi.PCFExecute(qmgr)

    changedProperties = []
    
    args = {pymqi.CMQC.MQCA_TOPIC_NAME: topic[pymqi.CMQC.MQCA_TOPIC_NAME], 
            pymqi.CMQC.MQIA_TOPIC_TYPE : pymqi.CMQC.MQTOPT_LOCAL}
    
    try:
        response = pcf.MQCMD_INQUIRE_TOPIC(args)
        for topic_info in response:
            for property in topic.keys():
                if str(topic[property])!=str(topic_info[property]).strip():                    
                    changedProperties.append(property)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:            
            raise
    
    return changedProperties

def alter_topic(qmgr,topic,changedProperties):    

    changedProperties.append(pymqi.CMQC.MQCA_TOPIC_NAME)
    changedProperties.append(pymqi.CMQC.MQIA_TOPIC_TYPE)
    
    args = {prop : topic[prop] for prop in changedProperties}
    
    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CHANGE_TOPIC(args)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def del_topic(qmgr,topic):    

    pcf = pymqi.PCFExecute(qmgr)

    args = {pymqi.CMQC.MQCA_TOPIC_NAME: topic[pymqi.CMQC.MQCA_TOPIC_NAME], 
            pymqi.CMQC.MQIA_TOPIC_TYPE : pymqi.CMQC.MQTOPT_LOCAL}
    
    try:
        pcf.MQCMD_DELETE_TOPIC(args)
        return True
    except pymqi.MQMIError as e:
        raise e
    
def create_topic(qmgr,topic):    

    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CREATE_TOPIC(topic)    
        return True
    except pymqi.MQMIError as e:
        raise e

def check_topic_exists(qmgr,topicName):    

    args = {pymqi.CMQC.MQCA_TOPIC_NAME: topicName}

    pcf = pymqi.PCFExecute(qmgr)

    try:
        response = pcf.MQCMD_INQUIRE_TOPIC(args)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:            
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
            topic_name=dict(required=True),
            topic_string=dict(required=True),
            publish=dict(default="enabled"), 
            subscribe=dict(default="enabled"),
            durable_sub=dict(default="enabled"),            
            persistence=dict(default="yes"),            
            state=dict(default="present")            
        )
    )  

    changed = False
    connected = False
    channel = module.params["channel"]
    topicDef = {
            pymqi.CMQC.MQCA_TOPIC_NAME : module.params["topic_name"],
            pymqi.CMQC.MQCA_TOPIC_STRING : module.params["topic_string"],                        
            pymqi.CMQC.MQIA_INHIBIT_PUB : TOPIC_PUB_MAP[module.params["publish"]],
            pymqi.CMQC.MQIA_INHIBIT_SUB : TOPIC_SUB_MAP[module.params["subscribe"]],
            pymqi.CMQC.MQIA_DURABLE_SUB : TOPIC_DUR_SUB_MAP[module.params["durable_sub"]],
            pymqi.CMQC.MQIA_TOPIC_DEF_PERSISTENCE : TOPIC_PERSISTENCE_MAP[module.params["persistence"]],
            pymqi.CMQC.MQIA_TOPIC_TYPE : pymqi.CMQC.MQTOPT_LOCAL
            }
    
    qmgr = pymqi.QueueManager(None)
    
    try:
        if channel['ssl']['enabled'] == 'yes':            
            cd, sco = getSecuredCDSCO(module.params["host"],channel)
            qmgr.connect_with_options(module.params["qmgrName"], cd, sco)
            connected = True
        else:            
            qmgr = pymqi.connect(module.params["qmgrName"], channel["name"], module.params["host"])   
            connected = True       
    
        exists = check_topic_exists(qmgr,module.params["topic_name"])    
    
        if not exists and module.params["state"] == 'present':
            create_topic(qmgr,topicDef)
            changed = True       
        elif exists and module.params["state"] == 'present' and len(wasChanged(qmgr,topicDef))>0:        
            alter_topic(qmgr,topicDef,wasChanged(qmgr,topicDef))
            changed = True
        elif exists and module.params["state"] == 'absent':
            del_topic(qmgr,topicDef)
            changed = True
    except pymqi.MQMIError as e:
        module.fail_json(msg=str(e),CC=e.comp,RC=e.reason)
    finally:   
        if connected:
            qmgr.disconnect()
    
    module.exit_json(changed=changed, exists=exists, qmgr=module.params["qmgrName"], topic=module.params["topic_name"])

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()
q
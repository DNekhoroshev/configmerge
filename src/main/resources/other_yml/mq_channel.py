#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import *
import pymqi
import os

"""
Ansible module to manage mq channels
(c) 2018, Nekhoroshev Dmitriy <Dmitry_Nekhoroshev@sberbank-cib.ru>
"""

EXAMPLES = '''
 - name: Create MQ channels
   become: yes
   become_user: mqm
   # Mandatory if you want to use SSL:
   environment:
        MQCLNTCF: '/var/mqm/mqclient.ini'    
        MQCLNTKEYREPODIR: '{{mqClient.baseDirectiory}}/ssl/client'      
   mq_channel:
        host: 'gmbus-mq-dev-01(1424)'
        qmgrName: 'GMSB_SEGMENT1_INOUT_DEV3'
        adm_channel: 'CIB.SVRCONN'
        channel_name: 'CIB.CHANNEL_TO_CREATE_OR_MODIFY_NAME'             
        mcauser: 'mqm'
        ssl_auth: 'optional'
        ssl_cipher_spec: 'TLS_RSA_WITH_AES_128_CBC_SHA256'
        ssl_peer: 'CN=IB*'
        state: 'present'
   register: mq_channel_update_result

 - name: Refreshing security 
   shell: "echo 'refresh security type({{item}})' | runmqsc {{mq_instance.name}}"   
   become: yes
   become_user: mqm
   ignore_errors: yes     
   with_items: '{{mq_channel_update_result.shouldRefresh}}'
'''

CHANNEL_TYPE_MAP = dict(
    svrconn = pymqi.CMQXC.MQCHT_SVRCONN,
    clntconn = pymqi.CMQXC.MQCHT_CLNTCONN,
    sender  = pymqi.CMQXC.MQCHT_SENDER,
    server  = pymqi.CMQXC.MQCHT_SERVER,
    receiver  = pymqi.CMQXC.MQCHT_RECEIVER,
    requester  = pymqi.CMQXC.MQCHT_REQUESTER,
    cluster_sender  = pymqi.CMQXC.MQCHT_CLUSSDR,
    cluster_receiver  = pymqi.CMQXC.MQCHT_CLUSRCVR
)

SSL_AUTH_TYPE_MAP = dict(    
    yes  = pymqi.CMQXC.MQSCA_REQUIRED,
    no  = pymqi.CMQXC.MQSCA_OPTIONAL
)

REFRESH_MAP = {
    pymqi.CMQCFC.MQIACH_SSL_CLIENT_AUTH : "SSL",
    pymqi.CMQCFC.MQCACH_SSL_CIPHER_SPEC : "SSL",
    pymqi.CMQCFC.MQCACH_SSL_PEER_NAME : "SSL",
    pymqi.CMQCFC.MQCACH_MCA_USER_ID : "AUTHSERV"
}

def refresh_security(qmgr,securityType):
    
    args = {pymqi.CMQCFC.MQIACF_SECURITY_TYPE : securityType}
    
    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_REFRESH_SECURITY(args)        
    except pymqi.MQMIError as e:
        raise e

def wasChanged(qmgr,channel):    

    pcf = pymqi.PCFExecute(qmgr)

    changedProperties = []
    
    args = {pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel[pymqi.CMQCFC.MQCACH_CHANNEL_NAME], 
            pymqi.CMQCFC.MQIACH_CHANNEL_TYPE : channel[pymqi.CMQCFC.MQIACH_CHANNEL_TYPE]}
    
    try:
        response = pcf.MQCMD_INQUIRE_CHANNEL(args)
        for channel_info in response:
            for property in channel.keys():
                if str(channel[property])!=str(channel_info[property]).strip():                    
                    changedProperties.append(property)
    except pymqi.MQMIError, e:
        if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:            
            raise
    
    return changedProperties


def alter_channel(qmgr,channel,changedProperties):    

    changedProperties.append(pymqi.CMQCFC.MQCACH_CHANNEL_NAME)
    changedProperties.append(pymqi.CMQCFC.MQIACH_CHANNEL_TYPE)
    
    refreshSet = set()
    for prop in changedProperties:
        if prop in REFRESH_MAP.keys():
            refreshSet.add(REFRESH_MAP[prop])
    
    args = {prop : channel[prop] for prop in changedProperties}
    
    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CHANGE_CHANNEL(args)        
        return refreshSet
    except pymqi.MQMIError as e:
        raise e

def create_channel(qmgr,channel):    

    pcf = pymqi.PCFExecute(qmgr)

    try:
        pcf.MQCMD_CREATE_CHANNEL(channel)            
    except pymqi.MQMIError as e:
        raise e

def del_channel(qmgr,channel):    

    pcf = pymqi.PCFExecute(qmgr)

    args = {pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel[pymqi.CMQCFC.MQCACH_CHANNEL_NAME]}
    
    try:
        pcf.MQCMD_DELETE_CHANNEL(args)        
    except pymqi.MQMIError as e:
        raise e
        
def check_channel_exists(qmgr,channel_name):
    args = {pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel_name}

    pcf = pymqi.PCFExecute(qmgr)

    try:
        response = pcf.MQCMD_INQUIRE_CHANNEL(args)
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
            adm_channel=dict(required=True,type="dict"),
            channel_name=dict(required=True),
            channel_type=dict(default="svrconn"),
            maxmsgl=dict(default=104857600),
            ssl_auth=dict(default="optional"),
            ssl_cipher_spec=dict(default=""),
            ssl_peer=dict(default=""),
            mcauser=dict(default=""),
            max_inst=dict(default=1000),
            max_inst_per_client=dict(default=500),
            state=dict(default="present")            
        )
    )  

    changed = False
    connected = False
    channel = module.params["adm_channel"]
    channelDef = {
            pymqi.CMQCFC.MQCACH_CHANNEL_NAME : module.params["channel_name"],
            pymqi.CMQCFC.MQIACH_CHANNEL_TYPE : CHANNEL_TYPE_MAP[module.params["channel_type"]],                        
            pymqi.CMQCFC.MQIACH_MAX_MSG_LENGTH : int(module.params["maxmsgl"]),
            pymqi.CMQCFC.MQIACH_SSL_CLIENT_AUTH : SSL_AUTH_TYPE_MAP[module.params["ssl_auth"]],
            pymqi.CMQCFC.MQCACH_SSL_CIPHER_SPEC : module.params["ssl_cipher_spec"],
            pymqi.CMQCFC.MQCACH_SSL_PEER_NAME : module.params["ssl_peer"],
            pymqi.CMQCFC.MQCACH_MCA_USER_ID : module.params["mcauser"],
            pymqi.CMQCFC.MQIACH_MAX_INSTANCES : int(module.params["max_inst"]),
            pymqi.CMQCFC.MQIACH_MAX_INSTS_PER_CLIENT : int(module.params["max_inst_per_client"])
            }
    
    qmgr = pymqi.QueueManager(None)
    exists = False
    refreshSet = set()
    try:
        if channel['ssl']['enabled'] == 'yes':            
            cd, sco = getSecuredCDSCO(module.params["host"],channel)
            qmgr.connect_with_options(module.params["qmgrName"], cd, sco)
            connected = True
        else:            
            qmgr = pymqi.connect(module.params["qmgrName"], channel["name"], module.params["host"])   
            connected = True       
    
        exists = check_channel_exists(qmgr,module.params["channel_name"])    
    
        if not exists and module.params["state"] == 'present':
            create_channel(qmgr,channelDef)
            changed = True       
        elif exists and module.params["state"] == 'present' and len(wasChanged(qmgr,channelDef))>0:        
            refreshSet = alter_channel(qmgr,channelDef,wasChanged(qmgr,channelDef))
            changed = True
        elif exists and module.params["state"] == 'absent':
            del_channel(qmgr,channelDef)
            changed = True
    except pymqi.MQMIError as e:
        module.fail_json(msg=str(e),CC=e.comp,RC=e.reason)
    finally:   
        if connected:
            qmgr.disconnect()
    
    module.exit_json(changed=changed, qmgr=module.params["qmgrName"], channel = module.params["channel_name"],shouldRefresh = refreshSet)

def debug(msg):
   print json.dumps({
      "DEBUG" : msg
   })

if __name__ == '__main__':
    main()
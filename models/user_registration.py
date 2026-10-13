
from datetime import datetime

class Registration:

    userid:int
    deviceid:str
    regist_type:int
    appid:str
    account:str
    password:str
    channel:str
    platform:str
    schema:str
    version_code:str
    createtime:datetime
    updatetime:datetime
    is_deleted:int
    is_enabled:int

    def __init__(self, userid:int, deviceid:str, regist_type:int, appid:str, account:str, password:str, channel:str, platform:str, schema:str, version_code:str, createtime:datetime, updatetime:datetime, is_deleted:int, is_enabled:int):
        self.userid = userid
        self.deviceid = deviceid
        self.regist_type = regist_type
        self.appid = appid
        self.account = account
        self.password = password
        self.channel = channel
        self.platform = platform
        self.schema = schema
        self.version_code = version_code
        self.createtime = createtime
        self.updatetime = updatetime
        self.is_deleted = is_deleted
        self.is_enabled = is_enabled

    def to_dict(self):
        return {
            "userid": self.userid,
            "deviceid": self.deviceid,
            "regist_type": self.regist_type,
            "appid": self.appid,
            "account": self.account,
            "password": self.password,
            "channel": self.channel,
            "platform": self.platform,
            "schema": self.schema,
            "version_code": self.version_code,
            "createtime": self.createtime.isoformat() if isinstance(self.createtime, datetime) else str(self.createtime),
            "updatetime": self.updatetime.isoformat() if isinstance(self.updatetime, datetime) else str(self.updatetime),
            "is_deleted": self.is_deleted,
            "is_enabled": self.is_enabled
        }   
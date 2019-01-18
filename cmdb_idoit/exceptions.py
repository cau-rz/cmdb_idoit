class CMDBRequestError(Exception):
    def __init__(self,message,errnr):
        self.message = message 
        self.errnr = int(errnr)

class CMDBNoneAPICategory(Exception):
    pass

class CMDBUnkownType(Exception):
    pass

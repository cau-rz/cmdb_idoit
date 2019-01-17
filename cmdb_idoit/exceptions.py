class CMDBRequestError(Exception):
    def __init__(self,message,errnr):
        self.message = message 
        self.errnr = errnr

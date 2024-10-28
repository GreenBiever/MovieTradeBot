class RefCodeException(BaseException):
    pass


class RefCodeCreationError(RefCodeException):

    def __init__(self, ref_code_name: str):
        self.ref_code_name = ref_code_name


class RefCodeAlreadyExists(RefCodeCreationError):

    def __init__(self, ref_code_name: str):
        super().__init__(f'Entity layer: Can not add new ref code {ref_code_name}, name already in use')


class RefCodeLimitReached(RefCodeCreationError):

    def __init__(self, ref_code_name: str):
        super().__init__(f'Entity layer: Can not add new ref code {ref_code_name}, code limit for user reached')

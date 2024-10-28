class RefCodeDbModelException(BaseException):
    pass


class RefCodeCreationError(RefCodeDbModelException):

    def __init__(self, ref_code_name: str):
        self.ref_code_name = ref_code_name


class RefCodeAlreadyExistsInDB(RefCodeCreationError):

    def __init__(self, ref_code_name: str):
        super().__init__(f'DB layer: Can not add new ref code {ref_code_name}, name already in use.')


class RefCodeLimitReached(RefCodeCreationError):

    def __init__(self, ref_code_name: str):
        super().__init__(f'DB layer: Can not add new ref code {ref_code_name}, limit reached.')
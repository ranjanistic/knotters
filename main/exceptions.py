class LocalStoreError(Exception):
    """Error with local storage"""
    pass


class DuplicateKeyError(LocalStoreError):
    """The given local store key already exists"""
    pass


class IllegalModeration(Exception):
    """The given moderation is illegal"""
    pass


class IllegalModerator(IllegalModeration):
    """The given profile is not allowed to be assigned moderation"""
    pass


class IllegalModerationType(IllegalModeration):
    """The given type of moderation is illegal"""
    pass


class IllegalModerationEntity(IllegalModeration):
    """The given entity for moderation is illegal"""
    pass


class IllegalModerationState(IllegalModeration):
    """The given state of moderation is illegal"""
    pass


class InvalidBaseProject(Exception):
    """The given state of moderation is illegal"""
    pass


class InactiveCompetitionError(Exception):
    """The given competition is inactive"""
    pass


class InvalidUserOrProfile(Exception):
    """The profile/user being accessed is not available or restricted or invalid"""
    pass

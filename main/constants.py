class NotificationCode():
    """Project Notifications = 1 """
    FREE_PROJ_CREATED = 1
    FREE_PROJ_DELETED = 1
    VERIF_PROJ_SUBMITTED = 1
    CORE_PROJ_SUBMITTED = 1
    VERIF_PROJ_APPROVED = 1
    CORE_PROJ_APPROVED = 1
    VERIF_PROJ_REJECTED = 1
    SNAPSHOT_CREATED = 1
    VERIF_PROJ_DELETION = 1
    VERIF_PROJ_DELETION_ACCEPTED = 1
    VERIF_PROJ_DELETION_REJECTED = 1
    CORE_PROJ_DELETION = 1
    CORE_PROJ_DELETION_ACCEPTED = 1
    CORE_PROJ_DELETION_REJECTED = 1
    GITHUB_BOT_INSTALLED = 1
    """Project Ownership Notifcations = 2 """
    PROJ_TRANSFER_INVITE = 2
    PROJ_TRANSFER_ACCEPTED = 2
    PROJ_TRANSFER_DECLINED = 2
    CO_BASE_PROJECT = 2
    CO_BASE_PROJECT_ACCEPTED = 2
    CO_BASE_PROJECT_REJECTED = 2
    """Moderator Transfer Notifications = 3"""
    PROJ_MOD_TRANSFER = 3
    PROJ_MOD_TRANSFER_ACCEPTED = 3
    PROJ_MOD_TRANSFER_REJECTED = 3
    CORE_PROJ_MOD_TRANSFER = 3
    CORE_PROJ_MOD_TRANSFER_ACCEPTED = 3
    CORE_PROJ_MOD_TRANSFER_REJECTED = 3
    """Competition status Notifications = 4"""
    PART_INVITE_ALERT = 4
    PART_WELCOME_ALERT = 4
    PART_JOINED_ALERT = 4
    PART_WITHDRAWN_ALERT = 4
    SUBM_CONFIRM_ALERT = 4
    """Competition Review Notifications = 5"""
    SUBM_MOD_ALERT = 5
    SUB_JUDGE_ALERT = 5
    """Competition Result Notifications = 6"""
    RES_DEC_ALERT = 6
    CERT_ALLOT_ALERT = 6
    RES_DEC_PART_ALERT = 6
    RES_DEC_JUDGE_ALERT = 6
    RES_DEC_MOD_ALERT = 6
    CLAIM_XP_COMPETITION = 6
    """Profile XP Notifications=7"""
    INCREASE_XP = 7
    DECREASE_XP = 7
    """Topic XP notifications =8"""
    INCREASE_BULK_XP_TOPIC = 8
    INCREASE_XP_IN_TOPIC = 8
    DECREASE_XP_IN_TOPIC = 8
    """Milestone Notifications = 9"""
    MILESTONE_NOTIF = 9
    MILESTONE_NOTIF_TOPIC = 9
    """Report Notifications = 10"""
    REPORTED_USER = 10
    REPORTED_PROJECT = 10
    REPORTED_SNAPSHOT = 10
    """Admire Notifications = 11"""
    ADMIRED_USER = 11
    ADMIRED_PROJECT = 11
    ADMIRED_COMPETITION = 11
    ADMIRED_SNAPSHOT = 11
    """Account Notifications = 12"""
    SUCCESSOR_INVITE = 12
    SUCCESSOR_ACCEPTED = 12
    SUCCESSOR_DECLINED = 12
    MIGRATION_PROBLEM = 12
    """Moderation Emails"""
    MODERATION_ASSIGNED = 13
    MODERATION_ACTION = 13
    UPGRADE_MODERATOR = 13

    """Management Notifications"""
    MANAGEMENT_INVITATION_ACCEPTED = 14
    ALERT_LEGAL_UPDATE = 14

    def getDetails(self):

        return [{
            "name": "Project Notifications",
            "code": self.FREE_PROJ_CREATED,
            "description": "Project is created, deleted or submitted"
        },
            {
            "name": "Project Ownership Notifications",
            "code": self.PROJ_TRANSFER_INVITE,
            "description": "Transfer of ownership of project"
        },
            {"name": "Moderator Transfer Notifications",
             "code": self. PROJ_MOD_TRANSFER,
             "description":  "Transfer of moderator of project"
             },

            {
            "name": "Competition status Notifications",
            "code": self.PART_INVITE_ALERT,
            "description": "Updates related to competitions"
        },
            {
            "name": "Competition Review Notifications",
            "code": self.SUBM_MOD_ALERT,
            "description": "Updates related to review of competitons"
        },
            {
            "name": "Competition Result Notifications",
            "code":  self.RES_DEC_ALERT,
            "description": "Updates related to competition results",
        },
            {
            "name": "Profile XP Notifications",
            "code":  self.INCREASE_XP,
            "description": "Updates related to changes in profile XP",
        },
            {
            "name": "Topic XP notifications",
            "code":  self.INCREASE_BULK_XP_TOPIC,
            "description": "Updates related to changes in topic XP",
        },
            {
            "name": "Milestone Notifications",
            "code":  self.MILESTONE_NOTIF,
            "description": "Updates related to milestones achieved",
        },
            {
            "name": "Report Notifications",
            "code":  self.REPORTED_USER,
            "description": "User, project or snapshot is reported",
        },
            {
            "name": "Admire Notifications",
            "code":  self.ADMIRED_USER,
            "description": "User, project or snapshot is admired",
        },

            {
            "name": "Account Notifications",
            "code":  self.SUCCESSOR_INVITE,
            "description": "Account setting updates",
            "disabled": True
        },
            {
            "name": "Moderation Emails",
            "code":  self.MODERATION_ASSIGNED,
            "description": "Updates related to Moderation",
        },
            {
            "name": "Management Notifications",
            "code":  self. MANAGEMENT_INVITATION_ACCEPTED,
            "description": "Updates related to Management",
        },
        ]

    # names = ["Project Notifications", "Project Ownership Notifications",
    #          "Moderator Transfer Notifications", "Competition status Notifications", "Competition Review Notifications", "Competition Result Notifications", "Profile XP Notifications", "Topic XP notifications", "Milestone Notifications", "Report Notifications", "Admire Notifications", "Account Notifications", "Moderation Emails", "Management Notifications"]

    # description = ["Project is created, deleted or submitted", "Transfer of ownership of project",
    #                "Transfer of moderator of project", "Updates related to competitions", "Updates related to review of competitons", "Updates related to competition results", "Updates related to changes in profile XP", "Updates related to changes in topic XP", "Updates related to milestones achieved", "User, project or snapshot is reported", "User, project or snapshot is admired", "Account setting updates", "Updates related to Moderation", "Updates related to Management"]

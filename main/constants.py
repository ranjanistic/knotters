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
    """Moderation Emails = 13"""
    MODERATION_ASSIGNED = 13
    MODERATION_ACTION = 13
    UPGRADE_MODERATOR = 13

    """Management Notifications = 14"""
    MANAGEMENT_INVITATION_ACCEPTED = 14
    """Legal Updates = 15"""
    ALERT_LEGAL_UPDATE = 15

    def getDetails(self) -> list:
        """Returns a list of notification dict data
        primarily meant to be the source of notification types for everyone.

        This is also used to synchronize notifications in database.
        """
        return [{
            "name": "Projects updates",
            "code": self.FREE_PROJ_CREATED,
            "description": "Creation, deletion, submission, approval, snapshots, and other things."
        },{
            "name": "Projects Invitations",
            "code": self.PROJ_TRANSFER_INVITE,
            "description": "Ownership of a project is transferred or a co-creator is added to the project"
        },{
            "name": "Project moderator updates",
            "code": self. PROJ_MOD_TRANSFER,
            "description":  "Moderatiorship changes or moderator invitations, etc."
        },{
            "name": "Competition Participation updates",
            "code": self.PART_INVITE_ALERT,
            "description": "Participation, withdrawal, member invitations and other participation related updates."
        },{
            "name": "Competition Submission updates",
            "code": self.SUBM_MOD_ALERT,
            "description": "Status updates of your competition submissions in review procedure."
        },{
            "name": "Competition Results updates",
            "code":  self.RES_DEC_ALERT,
            "description": "Results declaration, certificate allotment, xp claimed and other perks related updates.",
        },{
            "name": "Profile XP Updates",
            "code":  self.INCREASE_XP,
            "description": "Gained or lost XPs in profile.",
        },{
            "name": "Topic XP Updates",
            "code":  self.INCREASE_BULK_XP_TOPIC,
            "description": "Gained or lost XPs in topics.",
        },{
            "name": "Achievements and Milestones",
            "code":  self.MILESTONE_NOTIF,
            "description": "Achieved a new milestone in terms of XPs, or any other achievements.",
        },{
            "name": "Reports or Guideline violations",
            "code":  self.REPORTED_USER,
            "description": "Follow ups on your reportings, or reports against you or your content.",
        },{
            "name": "Admirations",
            "code":  self.ADMIRED_USER,
            "description": "Someone admires you, your project, your snapshot, your anything.",
        },{
            "name": "Account Legacy Updates",
            "code":  self.SUCCESSOR_INVITE,
            "description": "Successorship status, invites to you or by you and their relevant actions events.",
            "disabled": True
        },{
            "name": "Moderation Updates",
            "code":  self.MODERATION_ASSIGNED,
            "description": "Assigned moderation, action taken, and related moderator events.",
        },{
            "name": "Management Membership Events",
            "code":  self. MANAGEMENT_INVITATION_ACCEPTED,
            "description": "Organization membership realated updates.",
        },{
            "name": "Legal Updates",
            "code":  self.ALERT_LEGAL_UPDATE,
            "description": "Changes in policies, terms and conditions or other legalities from our side.",
        }
    ]

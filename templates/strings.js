{% load i18n %}
{% load l10n %}

const STRING = {
    static_cache_name: `static-cache-{{VERSION}}`,
    dynamic_cache_name: `dynamic-cache-{{VERSION}}`,
    updating: `{% trans "Updating..." %}`,
    okay: `{% trans "Okay" %}`,
    update_supressed: `{% trans "Okay, we won\'t remind you in this session." %}`,
    internal_error: `{% trans "An internal error occurred. We humbly request you to reload this page." %}`,
    app_update_success: `{% trans "App updated successfully." %}`,
    app_install_success: `{% trans "App installed successfully." %}`,
    browser_outdated: `{% trans "Your browser doesn\'t support some of our features ☹️. Please update/change your browser for the best experience." %}`,
    app_new_version_available: `{% blocktrans %}A new version of {{APPNAME}} is available{% endblocktrans %}`,
    with_new_features: `{% trans "with new features" %}`,
    perf_improvements: `{% trans "performance improvements" %}`,
    shall_we_update: `{% trans "Shall we update?" %}`,
    updates_are_imp: `{% trans "Updates are important." %}`,
    will_take_few_seconds: `{% trans "It will take a few seconds, depending upon your network strength." %}`,
    yes_up_now: `{% trans "Yes, update now" %}`,
    not_now: `{% trans "No, not now" %}`,
    re_introduction: `{% trans "Press Alt+R for re-introduction, or visit About Knotters page." %}`,
    update_available: `{% trans "Update available" %}`,
    default_error_message: `{% trans "Something went wrong." %}`,
    default_success_message: `{% trans "Successfull" %}`,
    network_error_message: `{% trans "Network error, check your connection." %}`,
    required: `{% trans "required" %}`,
    crop_image: `{% trans "Crop Image" %}`,
    img_too_large_10M: `{% trans "Image too large. Preferred size < 10 MB" %}`,
    file_too_large_10M: `{% trans "File too large. Preferred size < 10 MB" %}`,
    cancel: `{% trans "Cancel" %}`,
    confirm: `{% trans "Confirm" %}`,
    loading_image: `{% trans "Loading image..." %}`,
    sys_share_unavailable: `{% trans "Sharing not available on your system." %}`,
    file_to_base64_error: `{% trans "Failed to process file" %}`,
    limit_exceeded: `{% trans "Limit Exceeded" %}`,
    logout_failed: `{% trans "Failed to logout" %}`,
    logout_success: `{% trans "Logged out successfully" %}`,
    copied_to_clipboard: `{% trans "Copied to clipboard" %}`,
    copied_to_clipboard_error: `{% trans "Failed to copy to clipboard" %}`,
    try_that_again: `{% trans "Try that again?" %}`,
    take_me_to_appname: `{% blocktrans %}Take me to Knotters{% endblocktrans %}`,
    stay_in_appname: `{% blocktrans %}I\'ll stay in {{APPNAME}}{% endblocktrans %}`,
    remember_using_appname: `{% blocktrans %}Remember, you\'re using {{APPNAME}}, not Knotters!{% endblocktrans %}`,
    glad_to_help: `{% trans "Glad we could help 😊! Do not hesitate to contact us anytime." %}`,
    sorry_couldnt_help: `{% trans "We\'re sorry to hear that. You may submit a report, or reach us via our social channels or email." %}`,
    click_to_report: `{% trans "Click here to report." %}`,
    problem_solved: `{% trans "Problem solved!" %}`,
    problem_unsolved: `{% trans "I still have problems" %}`,
    blocking: `{% trans "Blocking..." %}`,
    no_wait: `{% trans "No, wait!" %}`,
    yes_block: `{% trans "Yes, block!" %}`,
    blocked: `{% trans "Blocked" %}`,
    block: `{% trans "block" %}`,
    got_it: `{% trans "Got it!" %}`,
    close_preview_img_help: `{% trans "Click anywhere around the image to close preview." %}`,
    you_sure_to: `{% trans "Are you sure you want to" %}`,
    you_can_unblock_from: `{% trans "You can unblock them anytime from your profile\'s privacy settings." %}`,
    leave_it: `{% trans "Leave it" %}`,
    link_gh_account: `{% trans "Link Github Account" %}`,
    gh_id_required: `{% trans "GitHub ID required" %}`,
    must_link_gh_account: `{% blocktrans %}Your GitHub identity must be linked with {{APPNAME}} for this action.{% endblocktrans %}`,
    troubleshooting: `{% trans "Troubleshooting" %}`,
    retry: `{% trans "Retry" %}`,
    oops_something_went_wrong: `{% trans "Oops! Something went wrong." %}`,
    theme_set_sys_default: `{% trans "Theme set to system default" %}`,
    use: `{% trans "Use" %}`,
    to_toggle_it: `{% trans "to toggle it." %}`,
    subscribed_to_notif_of: `{% trans "Successfully subscribed to notifications of" %}`,
    subscription_unavailable: `{% trans "Subscription unavailable" %}`,
    unsubscribed_from_notif_of: `{% trans "Successfully unsubscribed from notifications of" %}`,
    report: `{% trans "Report" %}`,
    feedback: `{% trans "Feedback" %}`,
    received_and_noted: `{% trans "received and will be looked into." %}`,
    or: `{% trans "or" %}`,
    your_id_remain_private: `{% trans "Your identity will remain private." %}`,
    optional: `{% trans "optional" %}`,
    your_name: `{% trans "Your name (or organization name)" %}`,
    your_email_addr: `{% trans "Your email address (we will contact you on this)" %}`,
    explain_in_detail: `{% trans "Explain everything here in detail" %}`,
    short_desc: `{% trans "Short description" %}`,
    short_desc_required: `{% trans "Short description required" %}`,
    send: `{% trans "Send" %}`,
    submitting: `{% trans "Submitting" %}`,
    select_category: `{% trans "Select category" %}`,
    reporting: `{% trans "Reporting..." %}`,
    reported: `{% trans "Reported" %}`,
    we_will_investigate: `{% trans "We\'ll investigate." %}`,
    delete: `{% trans "Delete" %}`,
    snapshot: `{% trans "Snapshot" %}`,
    delete_the_snap: `{% trans "delete the snapshot" %}`,
    yes_del: `{% trans "Yes, delete" %}`,
    no_snapshots: `{% trans "No snapshots" %}`,
    no_more_snaps: `{% trans "No more snapshots" %}`,
    creating_project: `{% trans "Creating project..." %}`,
    click_bubble_choose_lic: `{% trans "Click on a license bubble to choose one." %}`,
    some_val_invalid: `{% trans "Some values are invalid." %}`,
    refresh_n_startover: `{% trans "Please refresh and start over." %}`,
    pl_accept_terms: `{% trans "Please check the acceptance of terms checkbox at bottom." %}`,
    next: `{% trans "Next" %}`,
    submit: `{% trans "Submit" %}`,
    add_cust_lic: `{% trans "Add custom license" %}`,
    lic_name_required: `{% trans "License name required" %}`,
    lic_desc_required: `{% trans "License description required" %}`,
    lic_text_required: `{% trans "License text required" %}`,
    create_lic: `{% trans "Create license" %}`,
    lic_created: `{% trans "License created" %}`,
    upto_5_topics_allowed: `{% trans "Up to 5 topics allowed" %}`,
    upto_3_topics_allowed: `{% trans "Up to 3 topics allowed" %}`,
    upto_5_tags_allowed: `{% trans "Up to 5 tags allowed" %}`,
    deactivate_appname_account: `{% blocktrans %}Deactivate your {{APPNAME}} account?{% endblocktrans %}`,
    can_reactivate_anytime: `{% trans "You can reactivate your account by logging in again anytime." %}`,
    deactive_profile_url_wont_work: `{% trans "This also implies that your profile URL will not work during this period of deactivation." %}`,
    account_hidden_from_all: `{% trans "Your account will NOT get deleted, instead, it will be hidden from everyone." %}`,
    de_activate: `{% trans "de-activate" %}`,
    your_acc: `{% trans "your account" %}`,
    deactivate_my_acc: `{% trans "Deactivate my account" %}`,
    deactivating_acc: `{% trans "Deactivating account..." %}`,
    acc_deactivated: `{% trans "Your account has been deactivated." %}`,
    no_go_back: `{% trans "No, go back!" %}`,
    unable_to_sub_device_notif: `{% trans "Unable to subscribe to device notifications. Please check our notification permissions and try again." %}`,
    unable_to_sub_device_notif: `{% trans "Unable to subscribe to device notifications. Please check our notification permissions and try again." %}`,
    unable_to_unsub_device_notif: `{% trans "Unable to unsubscribe from device notifications." %}`,
    contact_us: `{% trans "Contact Us" %}`,
    dont_hesitate_contact_us: `{% trans "Please do not hesitate to contact us anytime😊!" %}`,
    contact_reason_required: `{% trans "Please select a reason to contact us" %}`,
    your_email_required: `{% trans "Your valid email address is needed for this." %}`,
    your_name_required: `{% trans "Your name is needed for this." %}`,
    contact_message: `{% trans "Your additional details and reasons to contact us." %}`,
    contact_message_required: `{% trans "Please describe your message to contact us." %}`,
    contact_request_received: `{% trans "We have received your request, and we'll reach out to you on your email shortly!😊" %}`,
    password_to_continue: `{% trans "Please provide your account password to continue" %}`,
    reauth_to_continue: `{% trans "Please re-authenticate to continue" %}`,
    password_required: `{% trans "Your account password is required" %}`,
    password_or_2fa_required: `{% trans "Please provide password or 2FA" %}`,
    password: `{% trans "Password" %}`,
    two_fa_token_or_backup: `{% trans "2FA or backup token" %}`,
    continue: `{% trans "Continue" %}`,
    asset_file_required: `{% trans "Asset file required" %}`,
    asset_name_required: `{% trans "Asset name required" %}`,
    compete_admire_success: `{% trans "You'll receive the latest updates in this competition now." %}`,

    //server side allowed messages
    india_first: `{% trans "India's first open source collaborative community platform. Be a part of Knotters community and explore what everyone's involved into." %}`,
    an_error: `{% trans "An error occurred." %}`,
    invalid_request: `{% trans "Invalid request" %}`,
    you_ve: `{% trans "You've accepted the terms and conditions." %}`,
    invalid_response: `{% trans "Invalid response" %}`,
    invalid_credentials: `{% trans "Invalid credentials" %}`,
    saved: `{% trans "Saved" %}`,
    profile_updated: `{% trans "Profile updated, it might take some time for changes to appear." %}`,
    tags_updated: `{% trans "Tags updated." %}`,
    topics_updated: `{% trans "Topics updated." %}`,
    no_topics: `{% trans "No topics selected" %}`,
    maximum_tags: `{% trans "Maximum tags limit reached." %}`,
    no_tags: `{% trans "No tags selected" %}`,
    maximum_topics: `{% trans "Maximum topics limit reached." %}`,
    please_login: `{% trans "Please login to continue." %}`,
    results_declared: `{% trans "Results declared!" %}`,
    results_not: `{% trans "Results not declared." %}`,
    results_declaration: `{% trans "Results declaration in progress" %}`,
    you_re: `{% trans "You're already participating." %}`,
    participation_confirmed: `{% trans 'Participation confirmed!' %}`,
    you_are: `{% trans 'You are currently not allowed to participate.' %}`,
    participation_withdrawn: `{% trans 'Participation withdrawn.' %}`,
    member_removed: `{% trans 'Member removed' %}`,
    invalid_ID: `{% trans 'Invalid ID' %}`,
    user_doesn: `{% trans "User doesn\'t exist." %}`,
    user_already: `{% trans "User already participating or invited." %}`,
    invitation_not_exists: `{% trans "Invitation does not exists" %}`,
    already_submitted: `{% trans "Already submitted" %}`,
    submitted_successfully: `{% trans "Submitted successfully" %}`,
    submitted_but: `{% trans "Submitted, but late." %}`,
    it_is: `{% trans "It is too late now." %}`,
    invalid_submission: `{% trans "Invalid submission markings, try again." %}`,
    error_in: `{% trans "Error in submission" %}`,
    no_moderators: `{% trans "No moderators in available your organization" %}`,
    project_created: `{% trans "Project created successfully!" %}`,
    sent_for: `{% trans "Sent for review" %}`,
    project_deleted: `{% trans "Project deleted" %}`,
    you_have: `{% trans "You have not accepted the terms" %}`,
    you_have: `{% trans "You have to choose a license" %}`,
    the_nickname: `{% trans "The nickname is not available, try something else." %}`,
    the_codename: `{% trans "The codename is not available, try something else." %}`,
    invalid_license: `{% trans 'Invalid license data' %}`,
    snapshot_published: `{% trans "Snapshot published" %}`,
    snapshot_updated: `{% trans "Snapshot updated" %}`,
    snapshot_removed: `{% trans "Snapshot removed" %}`,
    currently_under: `{% trans "Currently under moderation" %}`,
    already_resolved: `{% trans "Already resolved" %}`,
    already_exists: `{% trans "Already exists" %}`,
    request_message: `{% trans "Request message saved" %}`,
    response_message: `{% trans "Response message saved" %}`,
    re_applied: `{% trans "Re-applied for moderation to another moderator." %}`,
    setting_up: `{% trans "Setting up approved project." %}`,
    approved_project: `{% trans "Approved project setup done." %}`,
    github_repository: `{% trans "GitHub repository has not been setup yet. Check again later." %}`,
    no_GitHub: `{% trans "No GitHub organization has been linked." %}`,
    no_GitHub: `{% trans "No GitHub account has been linked." %}`,
    account_preferences: `{% trans "Account preferences saved." %}`,
    your_successor: `{% trans 'Your successor should have Github profile linked to their account.' %}`,
    you_are: `{% trans 'You are the successor of this profile.' %}`,
    successor_not: `{% trans 'Successor not found' %}`,
    successor_not: `{% trans 'Successor not set, use default successor if none.' %}`,
    you_ve: `{% trans "You\'ve declined this profile\'s successorship" %}`,
    you_re: `{% trans "You\'re now the successor of this profile\'s assets." %}`,
    account_deactivated: `{% trans "Account deactivated." %}`,
    account_deleted: `{% trans "Account deleted successfully." %}`,
    profile_XP: `{% trans "Profile XP increased" %}`,
    unauthorized_access: `{% trans 'Unauthorized access' %}`,
    invalid_moderator: `{% trans 'Invalid moderator' %}`,
    competition_with: `{% trans 'Competition with similar title exists' %}`,
    timings_are: `{% trans 'Timings are abnormal, please correct them' %}`,
    the_qualifier: `{% trans 'The qualifier rank is not valid. Use rank > 0 or 1' %}`,
    moderator_and: `{% trans 'Moderator and judges should be different' %}`,
    competition_created: `{% trans "Competition created successfully" %}`,
    certificates_generated: `{% trans 'Certificates generated successfully.' %}`,
    certificates_are: `{% trans 'Certificates are being generated.' %}`,
    certificate_not: `{% trans 'Certificate not found' %}`,
    that_moderation: `{% trans "That moderation was passed on to another moderator." %}`,
    no_moderators: `{% trans "No moderators available" %}`,
    you_have: `{% trans "You have successfully paid the registration fee" %}`,
    invitation_already: `{% trans "Invitation already exists" %}`,
    you_re_now_owner_of_project: `{% trans "You\'re now the owner of this project." %}`,
    you_ve_declined_ownership_project: `{% trans "You\'ve declined the ownership of this project." %}`,
    you_ve_accepted_the_invite: `{% trans "You\'ve accepted the invite" %}`,
    you_ve_declined_the_invite: `{% trans "You\'ve declined the invite" %}`,
    you_re_now_moderator_of_project: `{% trans "You\'re now the moderator of this project." %}`,
    you_ve_declined_moderatorship_of_project: `{% trans "You\'ve declined the moderatorship of this project." %}`,
    you_ve_accepted_delete_the_project: `{% trans "You\'ve accepted to delete the project." %}`,
    you_ve_declined_delete_this_project: `{% trans "You\'ve declined to delete this project." %}`,
    user_already_invited: `{% trans "User already invited." %}`,
    you_ve_joined_org: `{% trans "You\'ve joined this organization." %}`,
    you_ve_declined_org: `{% trans "You\'ve declined invitation to join this organization." %}`,
    pending_unresolved: `{% trans "Pending unresolved moderation requests exist." %}`,
    leave_moderation: `{% trans "Your Moderatorship has been revoked." %}`,
    nickname_updated: `{% trans "Nickname updated successfully." %}`,
    resolve_pending: `{% trans "Please resolve your pending moderations first." %}`,
    moderation_paused: `{% trans "Moderation Paused." %}`,
    moderation_resumed: `{% trans "Moderation Resumed." %}`,
    article_deleted: `{% trans "Article deleted successfully." %}`,
    article_drafted: `{% trans "Article drafted successfully." %}`,
    article_published: `{% trans "Article published successfully." %}`,
};
Object.freeze(STRING);

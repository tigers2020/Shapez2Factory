"""django-allauth socialaccount form tweaks (see SOCIALACCOUNT_FORMS in settings)."""

from __future__ import annotations

from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.socialaccount.forms import SignupForm as AllauthSocialSignupForm
from django import forms
from django.core.exceptions import ValidationError


class SocialSignupForm(AllauthSocialSignupForm):
    """Do not re-prompt for username when the provider value already passes validation.

    The social completion page is usually shown for email issues (e.g. address already
    registered). Google (and others) still supply a suggested username; if it is
    acceptable to ``clean_username``, we keep it in a hidden input so the user only
    deals with the fields that actually need attention (typically email).
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)

        username_init = (self.initial.get("username") or "").strip()
        if not username_init or "username" not in self.fields:
            return
        try:
            get_account_adapter().clean_username(username_init)
        except ValidationError:
            return
        self.fields["username"].widget = forms.HiddenInput()
        self.fields["username"].required = True

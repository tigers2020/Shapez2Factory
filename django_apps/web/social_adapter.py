"""django-allauth socialaccount adapter (see SOCIALACCOUNT_ADAPTER in settings)."""

from __future__ import annotations

from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Trusted OAuth (Google): match verified provider email to an existing user.

    With ``SOCIALACCOUNT_EMAIL_AUTHENTICATION``, allauth logs in that user instead of
    sending them to the social signup form. We then ensure an ``EmailAddress`` row
    exists and is ``verified=True`` so ``wipe_password`` does not clear a usable
    password for accounts created via username/password signup.
    """

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        super().pre_social_login(request, sociallogin)

        matched = getattr(sociallogin, "_did_authenticate_by_email", None)
        user = sociallogin.user
        if not matched or not user or not user.pk:
            return

        email = matched.lower()
        row = EmailAddress.objects.filter(user_id=user.pk, email__iexact=email).first()
        if row is not None:
            if not row.verified:
                row.verified = True
                row.save(update_fields=["verified"])
            return

        has_primary = EmailAddress.objects.filter(user_id=user.pk, primary=True).exists()
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=not has_primary,
            verified=True,
        )

from django.shortcuts import redirect


class FirstLoginPasswordChangeMiddleware:
    """Force new users to change password on first login."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            profile = self._get_profile(request)
            if profile is None:
                return self.get_response(request)

            # If user just changed password, clear flag and go to app home
            if request.path_info == '/admin/password_change/done/':
                if profile.must_change_password:
                    profile.must_change_password = False
                    profile.save()
                return redirect('/')

            # Redirect to password change if needed
            if profile.must_change_password:
                path = request.path_info
                allowed_paths = [
                    '/admin/password_change/',
                    '/admin/password_change/done/',
                    '/admin/logout/',
                ]
                if not any(p in path for p in allowed_paths):
                    return redirect('admin:password_change')

        return self.get_response(request)

    def _get_profile(self, request):
        """Get or create a user profile."""
        try:
            return request.user.profile
        except Exception:
            from .models import UserProfile
            try:
                return UserProfile.objects.create(
                    user=request.user, must_change_password=False
                )
            except Exception:
                return None

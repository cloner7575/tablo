---
name: django-auth
description: Django authentication, authorization, custom user models, and optional JWT (SimpleJWT). Use when implementing login, permissions, AUTH_USER_MODEL, sessions, or token auth.
---

# Django Auth

## Custom User

This starter already ships `apps.accounts.models.User` as `AUTH_USER_MODEL`. Keep it. Add profile fields on that model or a related profile; do not introduce a second user table.

```python
# apps/accounts/models.py
class User(AbstractUser):
    class Meta:
        db_table = "users"
```

Never switch to `django.contrib.auth.models.User` in a derived project.

## Screens already shipped

`apps/accounts` serves the whole password lifecycle at `/accounts/`, with
templates in `templates/registration/`:

| Route name | Screen |
|---|---|
| `accounts:login` | sign in (`LoginForm`, autocomplete attributes) |
| `accounts:logout` | POST-only sign out (the header form) |
| `accounts:password_change[_done]` | change while signed in |
| `accounts:password_reset[_done/_confirm/_complete]` | forgotten password |

`LOGIN_URL` is `accounts:login`, so `@login_required` lands somewhere real
instead of the admin. The reset email template is overridden because Django's
default reverses an unnamespaced `password_reset_confirm`, which does not exist
here — keep `{% url 'accounts:password_reset_confirm' %}` if you edit it.

Registration/signup is deliberately **not** shipped: who may create an account
is a product decision. Add a `SignupView` + `UserCreationForm` in `accounts`
when the product needs one, and rate-limit it.

## Views and Decorators

- `@login_required` / `@permission_required` for template views
- `LoginRequiredMixin` / `PermissionRequiredMixin` for CBVs
- `request.user.is_authenticated` before touching user fields
- Check object ownership in the view or a custom permission, not only in the template

```python
@login_required
def post_edit(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)
    if not post.is_editable_by(request.user):
        raise PermissionDenied
    ...
```

Put `is_editable_by` on the model (fat models).

## Permissions and Groups

- Use Django permissions for admin and coarse gates
- Use model methods / custom DRF permissions for domain rules
- Do not scatter `if user.is_superuser` through views; superuser is an escape hatch, not the product model

## JWT (optional)

SimpleJWT is not installed. Add it only for token APIs:

```bash
.venv/bin/pip install djangorestframework-simplejwt
```

- Access tokens short-lived; refresh rotated when possible
- Put secrets in env (`SIGNING_KEY` must not be hardcoded)
- Prefer `Authorization: Bearer` header; do not put JWTs in localStorage if an XSS-prone template app shares the origin — httpOnly cookies + CSRF is safer for browser apps
- Still authenticate the queryset (`get_queryset` scoped to user). A valid token is not authorization for every row.

## Passwords and Sessions

- Never log passwords or tokens
- Use Django password validators (already in `core/settings/base.py`)
- `DEBUG=False` + secure cookies before production: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`

## Anti-Patterns

- Rolling a custom password hasher or token format
- Trusting hidden form fields for `user_id`
- `authenticate()` then `login()` without checking `is_active`
- Storing JWTs in the database "just in case" without a revocation story

## Integration

- `django-rest-framework`, `django-admin`, `django-models`, `pytest-django-patterns`

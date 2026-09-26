---
name: django-forms
description: Django form handling patterns including ModelForm, validation, clean methods, and HTMX form submission. Use when building forms, implementing validation, or handling form submission.
---

# Django Forms

## Philosophy

- Prefer ModelForm for model-backed forms
- Keep validation in forms, not views
- Always handle and display form errors
- Use `commit=False` when you must set extra fields before save

## Validation

**Field-level** (`clean_<field>`):

- Validate and transform a single field
- Return the cleaned value or raise `ValidationError`

**Cross-field** (`clean`):

- Call `super().clean()` first
- Read fields from `cleaned_data`
- Use `self.add_error(field, message)` for field-specific errors

## View Integration

```python
def create_post(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:detail", pk=post.pk)
    else:
        form = PostForm()

    return render(request, "posts/create.html", {"form": form})
```

HTMX: check `request.headers.get("HX-Request")`, return a partial on success/error, and use `HX-Trigger` to notify other components.

## Templates

- Render fields with `components/_field.html` — it already carries the label,
  required marker, help text, and the error ids Django's `aria-describedby`
  points at
- Show non-field errors with `partials/_form_errors.html` (`role="alert"`)
- Partials (`_form.html`) for HTMX responses
- Include `{% csrf_token %}` on POST forms
- Use `hx-indicator` and `hx-disabled-elt="this"` for HTMX submits

## Widgets and Formsets

- Override widgets in `Meta.widgets`
- `inlineformset_factory` for related collections
- Validate both: `form.is_valid() and formset.is_valid()`

## Pitfalls

- Validating in views instead of forms
- Saving without `is_valid()`
- Forgetting `commit=False` when setting related fields
- Not displaying errors to the user

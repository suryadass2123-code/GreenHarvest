
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'role': form.cleaned_data['role'].strip().lower()
                }
            )

            messages.success(
                request,
                'Registration successful. Please login.'
            )

            return redirect('login')

    else:
        form = RegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.is_superuser or user.is_staff:
                return redirect('home')

            try:
                profile = Profile.objects.get(user=user)
                role = (profile.role or '').strip().lower()
            except Profile.DoesNotExist:
                role = ''

            if role in {'farmer', 'customer'}:
                return redirect('home')

            messages.warning(
                request,
                'Your account role is not configured. Please contact the administrator.'
            )
            logout(request)
            return redirect('login')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'accounts/login.html')


@login_required
def role_dashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin_dashboard')

    try:
        profile = Profile.objects.get(user=request.user)
        role = (profile.role or '').strip().lower()
    except Profile.DoesNotExist:
        role = ''

    if role == 'farmer':
        return redirect('farmer_dashboard')

    if role == 'customer':
        return redirect('customer_dashboard')

    messages.error(request, 'Your account role is not configured.')
    logout(request)
    return redirect('login')


def user_logout(request):
    logout(request)
    return redirect('/')

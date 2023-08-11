from random import randint

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView, FormView

from users.forms import UserRegisterForm, UserProfileForm, UserResetPasswordForm
from users.models import User
from django.core.mail import send_mail


class ProfileView(UpdateView):
    model = User
    form_class = UserProfileForm
    success_url = reverse_lazy('catalog:main')

    def get_object(self, queryset=None):
        return self.request.user


class RegisterView(CreateView):
    """
    Класс для регистрации пользователя на сайте.
    """
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy('users:email_confirmation')

    def form_valid(self, form):
        user = form.save()
        user.rand_key = randint(1, 2147483644)
        user.save()
        verify_url = reverse('users:verify_email', args=[user.rand_key])
        verify_link = self.request.build_absolute_uri(verify_url)
        send_mail(
            'Подтвердите свой электронный адрес',
            f'Пожалуйста, перейдите по следующей ссылке, чтобы подтвердить свой адрес электронной почты: {verify_link}',
            'test',
            [user.email],
            fail_silently=False
        )
        return super().form_valid(form)


class VerifyEmailView(View):
    def get(self, request, rand_key):
        try:
            user = User.objects.get(rand_key=rand_key)
            user.is_active = True
            user.save()
            return HttpResponseRedirect(reverse('users:email_confirmed'))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('users:email_confirmation_failed'))


class ResetPasswordView(FormView):
    """
    Класс для сброса пароля на автоматически сгенерированный
    """
    model = User
    template_name = 'users/reset_password.html'
    form_class = UserResetPasswordForm
    success_url = reverse_lazy('users:reset_password_done')

    def form_valid(self, form):
        email = form.cleaned_data['username']
        try:
            user = User.objects.get(email=email)
            new_password = User.objects.make_random_password(length=12)
            user.set_password(new_password)
            user.save()
            send_mail(
                'Сброс пароля',
                f'Ваш новый пароль для входа: {new_password}',
                'test',
                [user.email],
                fail_silently=False
            )
        except User.DoesNotExist:
            return redirect('users:reset_password_failed')
        return super().form_valid(form)


class EmailConfirmationView(TemplateView):
    template_name = 'users/email_confirmation_sent.html'


class EmailConfirmedView(TemplateView):
    template_name = 'users/email_confirmed.html'


class EmailConfirmationFailedView(TemplateView):
    template_name = 'users/email_confirmation_failed.html'
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import CustomUser, Project, Task


class CustomUserLoginForm(UserCreationForm):
    avatar = forms.ImageField(required=False)  # Додано поле для аватару

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'country', 'avatar', 'password')
        error_messages = {
            'email': {
                'required': 'Це поле є обов\'язковим',
            },
            'password': {
                'required': 'Це поле є обов\'язковим',
            },
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'country', 'avatar']
        error_messages = {
            'email': {
                'required': 'Це поле є обов\'язковим',
            },
            'first_name': {
                'required': 'Це поле є обов\'язковим',
            },
            'last_name': {
                'required': 'Це поле є обов\'язковим',
            },
            'phone_number': {
                'required': 'Це поле є обов\'язковим',
            },
            'country': {
                'required': 'Це поле є обов\'язковим',
            },

        }

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['email'].required = True
        self.fields['phone_number'].required = True
        self.fields['country'].required = True
        self.fields['last_name'].required = False
        self.fields['avatar'].required = False


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    COUNTRIES = [
        ('Ukraine', 'Україна'),
        ('USA', 'США'),
    ]
    country = forms.ChoiceField(choices=COUNTRIES)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'country', 'phone_number', 'password']
        error_messages = {
            'first_name': {
                'required': 'Це поле є обов\'язковим',
            },
            'last_name': {
                'required': 'Це поле є обов\'язковим',
            },
            'email': {
                'required': 'Це поле є обов\'язковим',
            },
            'country': {
                'required': 'Це поле є обов\'язковим',
            },
            'password': {
                'required': 'Це поле є обов\'язковим',
            },

        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number:
            raise ValidationError("Це поле є обов'язковим.")

        # Перевірка номера телефону
        if len(phone_number) < 10:
            raise ValidationError("Номер телефону повинен містити щонайменше 10 цифр.")

        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("Цей номер телефону вже зайнятий.")

        # Для українських номерів
        if self.cleaned_data.get('country') == "Ukraine":
            if not phone_number.startswith("+380"):
                raise ValidationError("Номер телефону для України повинен починатися з +380.")
            if len(phone_number) != 13:
                raise ValidationError("Номер телефону для України повинен містити 13 символів.")

        # Для американських номерів
        elif self.cleaned_data.get('country') == "USA":
            if not phone_number.startswith("+1"):
                raise ValidationError("Номер телефону для США повинен починатися з +1.")
            if len(phone_number) != 12:
                raise ValidationError("Номер телефону для США повинен містити 12 символів.")

        return phone_number



    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image']  # Вкажіть поля вашої моделі
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        error_messages = {
            'title': {
                'required': 'Це поле є обов\'язковим',
            },
            'description': {
                'required': 'Це поле є обов\'язковим',
            },
        }


class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image']
        error_messages = {
            'title': {
                'required': 'Це поле є обов\'язковим',
            },
            'description': {
                'required': 'Це поле є обов\'язковим',
            },
        }

class AddFriendForm(forms.Form):
    identifier = forms.CharField(
        max_length=255,  # Максимальна довжина повинна підходити як для телефону, так і для email
        label="Номер телефону або Email",
        widget=forms.TextInput(attrs={'placeholder': 'Введіть номер телефону або Email'})
    )

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'image', 'work_status', 'urgency_status', 'due_date']

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone_number, country, password=None, **extra_fields):
        if not email:
            raise ValueError('Користувач повинен мати пошту')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, phone_number=phone_number, country=country, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone_number, country, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперкористувач повинен мати is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперкористувач повинен мати is_superuser=True.')

        return self.create_user(email, first_name, last_name, phone_number, country, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(unique= True, max_length=15, blank=True)
    country = models.CharField(max_length=50)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    friends = models.ManyToManyField('self', symmetrical=False, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'country']

    def __str__(self):
        return self.email


class Project(models.Model):
    title = models.CharField(max_length=255)  # Назва проекту
    description = models.TextField()  # Опис проекту
    created_at = models.DateTimeField(auto_now_add=True)  # Час створення проекту
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='projects_owned')  # Користувач, який створив проект
    admins = models.ManyToManyField(CustomUser, related_name='projects_administered', blank=True)  # Адміністратори проекту
    users = models.ManyToManyField(CustomUser, related_name='projects_participated', blank=True)
    image = models.ImageField(upload_to='project_images/', blank=True, null=True)# Користувачі проекту

    def __str__(self):
        return self.title


class FriendRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    # Статуси за терміновістю
    URGENCY_CHOICES = [
        ('normal', 'Звичайне'),
        ('urgent', 'Терміново'),
        ('critical_urgent', 'Критично терміново'),
        ('overdue', 'Просрочене'),
    ]

    # Статуси за роботою
    WORK_STATUS_CHOICES = [
        ('on_inspection', 'На перевірці'),
        ('completed', 'Виконано'),
        ('in_process', 'В процесі'),
        ('postponed', 'Відкладено'),
        ('free', 'Вільно'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='task_images/', null=True, blank=True)
    # Поле для терміновості
    urgency_status = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal', null=True, blank=True)
    # Поле для статусу виконання
    work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, default='free', null=True, blank=True)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Comment(models.Model):
    content = models.TextField()  # Вміст коментаря
    created_at = models.DateTimeField(auto_now_add=True)  # Дата створення
    likes = models.IntegerField(default=0, unique=('comment', 'user'))  # Кількість лайків
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)  # Посилання на завдання
    user = models.ForeignKey(CustomUser, related_name='comments', on_delete=models.CASCADE)  # Користувач, який залишив коментар

    def __str__(self):
        return f'Comment by {self.user} on {self.task}'
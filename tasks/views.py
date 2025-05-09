from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import ListView
from .forms import CustomUserLoginForm, ProfileEditForm, RegistrationForm, ProjectForm, ProjectEditForm, AddFriendForm, \
    TaskForm, CommentForm, EditTaskForm
from .models import Project, CustomUser, FriendRequest, Task, Comment
from django.utils import timezone



@login_required(login_url='/login/')
def about(request):
    return render(request, 'tasks_html/about.html')

def usage_agreement(request):
    return render(request, 'tasks_html/usage_agreement.html')


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'tasks_html/home.html'
    context_object_name = 'projects'
    login_url = '/login/'
    paginate_by = 10

    def get_queryset(self):
        projects = Project.objects.filter(
            Q(owner=self.request.user) |
            Q(users=self.request.user) |
            Q(admins=self.request.user)
        ).distinct().order_by('-created_at')

        user_tasks = Task.objects.filter(assigned_user=self.request.user)

        query = self.request.GET.get('search')
        if query:
            user_tasks = user_tasks.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

        user_tasks = self.filter_by_date(user_tasks)
        user_tasks = self.filter_by_status(user_tasks)

        return projects, user_tasks

    def filter_by_date(self, user_tasks):
        due_date_from = self.request.GET.get('due_date_from')
        due_date_to = self.request.GET.get('due_date_to')

        if due_date_from:
            due_date_from_parsed = parse_date(due_date_from)
            if due_date_from_parsed:
                user_tasks = user_tasks.filter(due_date__gte=due_date_from_parsed)

        if due_date_to:
            due_date_to_parsed = parse_date(due_date_to)
            if due_date_to_parsed:
                user_tasks = user_tasks.filter(due_date__lte=due_date_to_parsed)

        return user_tasks

    def filter_by_status(self, user_tasks):
        urgency_status = self.request.GET.getlist('urgency_status')
        work_status = self.request.GET.getlist('work_status')

        if urgency_status:
            user_tasks = user_tasks.filter(urgency_status__in=urgency_status)

        if work_status:
            user_tasks = user_tasks.filter(work_status__in=work_status)

        return user_tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects, user_tasks = self.get_queryset()
        context['projects'] = projects
        context['user_tasks'] = user_tasks
        return context


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'tasks_html/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Перенаправлення на домашню сторінку
            else:
                form.add_error(None, 'Неправильний логін або пароль.')
    else:
        form = CustomUserLoginForm()

    return render(request, 'tasks_html/login.html', {'form': form})

@login_required
def edit_profile(request):
    user = request.user  # Отримуємо поточного користувача
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)  # Додано request.FILES
        if form.is_valid():
            form.save()  # Зберігаємо зміни
            return redirect('home')  # Перенаправлення на домашню сторінку або іншу сторінку
    else:
        form = ProfileEditForm(instance=user)  # Заповнюємо форму даними користувача

    return render(request, 'tasks_html/edit_profile.html', {'form': form})

@login_required(login_url='/login/')
def user_profile(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'tasks_html/user_profile.html', context)

@login_required(login_url='/login/')
def delete_profile(request):
    if request.method == 'POST':
        request.user.delete()  # Видалити користувача
        return redirect('home')  # Перенаправити на головну сторінку після видалення
    return redirect('user_profile')  # Відображення шаблону підтвердження

@login_required(login_url='/login/')
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)  # Не зберігаємо ще в базу
            project.owner = request.user  # Призначаємо користувача як власника проекту
            project.save()  # Тепер зберігаємо проект в базу

            # Додаємо користувача до адміністраторів проекту
            project.admins.add(request.user)

            return redirect('home')  # Перенаправляємо на головну сторінку після створення проекту
    else:
        form = ProjectForm()

    return render(request, 'tasks_html/create_project.html', {'form': form})


class ProjectDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        # Отримуємо адміністраторів та учасників проекту
        admins = project.admins.all()
        participants = project.users.exclude(id=project.owner.id)
        tasks = Task.objects.filter(project=project)

        query = self.request.GET.get('search')
        due_date_from = self.request.GET.get('due_date_from')
        due_date_to = self.request.GET.get('due_date_to')

        # Статуси терміновості та виконання
        urgency_status = self.request.GET.getlist('urgency_status')
        work_status = self.request.GET.getlist('work_status')

        user_tasks = tasks  # Початкове значення для фільтрації

        # Фільтрація по назві та опису
        if query:
            user_tasks = user_tasks.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

        # Фільтрація по датах
        if due_date_from:
            due_date_from_parsed = parse_date(due_date_from)
            if due_date_from_parsed:
                user_tasks = user_tasks.filter(due_date__gte=due_date_from_parsed)

        if due_date_to:
            due_date_to_parsed = parse_date(due_date_to)
            if due_date_to_parsed:
                user_tasks = user_tasks.filter(due_date__lte=due_date_to_parsed)

        # Фільтрація по статусу терміновості
        if urgency_status:
            user_tasks = user_tasks.filter(urgency_status__in=urgency_status)

        # Фільтрація по статусу виконання
        if work_status:
            user_tasks = user_tasks.filter(work_status__in=work_status)

        for task in user_tasks:  # Оновлюємо статус для відфільтрованих завдань
            self.update_task_status(task)

        context = {
            'project': project,
            'admins': admins,
            'participants': participants,
            'tasks': user_tasks,
        }

        return render(request, 'tasks_html/project_detail.html', context)

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        # Додавання адміністратора
        admin_identifier = request.POST.get('admin_identifier')  # Отримуємо ідентифікатор адміністратора
        friends_admin = request.POST.getlist('friends_admin')  # Отримуємо друзів, вибраних для додавання

        if friends_admin:
            for friend_id in friends_admin:
                try:
                    admin = CustomUser.objects.get(id=friend_id)

                    # Якщо користувач був учасником, видаляємо його з учасників
                    if admin in project.users.all():
                        project.users.remove(admin)  # Видаляємо з учасників
                        messages.info(request,
                                      f'Користувача {admin.first_name} {admin.last_name} видалено з учасників проекту.')

                    # Додаємо адміністратора
                    if admin == project.owner:
                        messages.error(request, 'Власника проекту не можна додати до адміністраторів.')
                    else:
                        project.admins.add(admin)  # Додаємо адміністратора
                        messages.success(request,
                                         f'Користувача {admin.first_name} {admin.last_name} додано до адміністраторів проекту.')
                except CustomUser.DoesNotExist:
                    messages.error(request, f'Користувача з ID {friend_id} не знайдено.')
        elif admin_identifier:
            try:
                if "@" in admin_identifier:
                    admin = CustomUser.objects.get(email=admin_identifier)
                else:
                    admin = CustomUser.objects.get(phone_number=admin_identifier)

                # Якщо користувач був учасником, видаляємо його з учасників
                if admin in project.users.all():
                    project.users.remove(admin)  # Видаляємо з учасників
                    messages.info(request,
                                  f'Користувача {admin.first_name} {admin.last_name} видалено з учасників проекту.')

                # Додаємо адміністратора
                if admin == project.owner:
                    messages.error(request, 'Власника проекту не можна додати до адміністраторів.')
                else:
                    project.admins.add(admin)  # Додаємо адміністратора
                    messages.success(request,
                                     f'Користувача {admin.first_name} {admin.last_name} додано до адміністраторів проекту.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Користувача з такою інформацією не знайдено.')
        else:
            admin_id = request.POST.get('admin_id')  # Отримуємо id адміністратора для видалення
            if admin_id:
                try:
                    admin = CustomUser.objects.get(id=admin_id)
                    if admin == project.owner:
                        messages.error(request, 'Власника проекту не можна видалити з адміністраторів.')
                    else:
                        project.admins.remove(admin)  # Видаляємо адміністратора
                        messages.success(request,
                                         f'Користувача {admin.first_name} {admin.last_name} видалено з адміністраторів проекту.')
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Користувача не знайдено.')

        # Додавання учасника
        identifier = request.POST.get('identifier')  # Отримуємо ідентифікатор (email або телефон)
        friends_user = request.POST.getlist('friends_user')  # Отримуємо друзів, вибраних для додавання

        if friends_user:
            for friend_id in friends_user:
                try:
                    user = CustomUser.objects.get(id=friend_id)

                    # Якщо користувач був адміністратором, видаляємо його з адміністраторів
                    if user in project.admins.all():
                        project.admins.remove(user)  # Видаляємо з адміністраторів
                        messages.info(request,
                                      f'Користувача {user.first_name} {user.last_name} видалено з адміністраторів проекту.')

                    # Додаємо учасника
                    project.users.add(user)
                    messages.success(request,
                                     f'Користувача {user.first_name} {user.last_name} додано до учасників проекту.')
                except CustomUser.DoesNotExist:
                    messages.error(request, f'Користувача з ID {friend_id} не знайдено.')
        elif identifier:
            try:
                if "@" in identifier:
                    participant = CustomUser.objects.get(email=identifier)
                else:
                    participant = CustomUser.objects.get(phone_number=identifier)

                # Якщо користувач був адміністратором, видаляємо його з адміністраторів
                if participant in project.admins.all():
                    project.admins.remove(participant)  # Видаляємо з адміністраторів
                    messages.info(request,
                                  f'Користувача {participant.first_name} {participant.last_name} видалено з адміністраторів проекту.')

                # Додаємо учасника
                project.users.add(participant)
                messages.success(request,
                                 f'Користувача {participant.first_name} {participant.last_name} додано до учасників проекту.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Користувача з такою інформацією не знайдено.')

        else:
            # Обробка видалення учасника
            participant_id = request.POST.get('participant_id')  # Отримуємо id учасника для видалення
            if participant_id:
                try:
                    participant = CustomUser.objects.get(id=participant_id)
                    project.users.remove(participant)  # Видаляємо учасника з проекту
                    messages.success(request,
                                     f'Користувача {participant.first_name} {participant.last_name} видалено з учасників проекту.')
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Користувача не знайдено.')

        if request.method == "POST":
            # Перевірка, чи це запит на видалення завдання
            if 'delete_task' in request.POST:
                task_id = request.POST.get('task_id')
                if task_id:
                    try:
                        task = Task.objects.get(id=task_id, project=project)
                        task.delete()
                        messages.success(request, 'Завдання успішно видалено.')
                    except Task.DoesNotExist:
                        messages.error(request, 'Завдання не знайдено.')

            # Перевірка, чи це запит на завершення завдання
            elif 'complete_task' in request.POST:
                task_id = request.POST.get('task_id')
                if task_id:
                    try:
                        task = Task.objects.get(id=task_id, project=project)
                        task.work_status = 'on_inspection'  # Змінюємо статус на 'На перевірці'
                        task.save()
                        messages.success(request, 'Завдання успішно завершено та відправлено на перевірку.')
                    except Task.DoesNotExist:
                        messages.error(request, 'Завдання не знайдено.')

            elif 'delete_complete_task' in request.POST:
                task_id = request.POST.get('task_id')
                if task_id:
                    try:
                        task = Task.objects.get(id=task_id, project=project)
                        task.work_status = 'postponed'  # Змінюємо статус на 'На перевірці'
                        task.save()
                        messages.success(request, 'Завдання успішно завершено та відправлено на перевірку.')
                    except Task.DoesNotExist:
                        messages.error(request, 'Завдання не знайдено.')

        return redirect('project_detail', pk=pk)

    def update_task_status(self, task):
        """
        Оновлює статус завдання на основі часу до дедлайну.
        """
        now = timezone.now()
        total_time = task.due_date - now  # Загальний час до дедлайну
        task_duration = task.due_date - task.created_at  # Припустимо, що у вас є поле created_at

        # Логіка зміни статусу
        if task.work_status != 'completed':
            if task.work_status != 'on_inspection':
                if total_time.total_seconds() <= 97200:  # 86400 секунд = 1 доба
                    task.urgency_status = 'critical_urgent'
                elif total_time.total_seconds() <= 0:
                    task.urgency_status = 'overdue'  # Якщо дедлайн пройшов
                else:
                    first_period = task_duration / 3
                    second_period = first_period * 2
                    time_left = task.due_date - now

                    if time_left <= first_period:
                        task.urgency_status = 'critical_urgent'
                    elif time_left <= second_period:
                        task.urgency_status = 'urgent'
                    else:
                        task.urgency_status = 'normal'

        task.save()


@login_required(login_url='/login/')
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner:
        return redirect('home')

    if request.method == 'POST':
        form = ProjectEditForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=project.pk)  # Редірект на деталі проекту після збереження
    else:
        form = ProjectEditForm(instance=project)

    # Передача змінної 'project' до шаблону
    return render(request, 'tasks_html/project_edit.html', {'form': form, 'project': project})


@login_required(login_url='/login/')
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.user != project.owner:
        return redirect('home')

    if request.method == 'POST':
        project.delete()
        return redirect('home')  # Редірект на головну сторінку після видалення
    return render(request, 'tasks_html/project_detail.html', {'project': project})


class FriendsView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'tasks_html/friends_list.html'
    context_object_name = 'friends'

    def get_queryset(self):
        user = self.request.user
        # Отримуємо список друзів
        queryset = user.friends.all()

        # Отримуємо значення параметра пошуку
        search_query = self.request.GET.get('search', '')

        if search_query:
            # Фільтруємо список друзів за іменем, прізвищем, поштою або номером телефону
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AddFriendForm()
        context['friend_requests'] = self.request.user.received_friend_requests.filter(status='pending')
        context['sent_requests'] = self.request.user.sent_friend_requests.filter(
            status='pending')  # Додаємо надіслані запити
        context['search_query'] = self.request.GET.get('search', '')  # Додаємо пошуковий запит до контексту
        return context

    def post(self, request, *args, **kwargs):
        form = AddFriendForm(request.POST)
        friends = self.get_queryset()  # Отримуємо список друзів для контексту
        friend_requests = self.request.user.received_friend_requests.filter(status='pending')  # Отримуємо запити дружби
        sent_requests = self.request.user.sent_friend_requests.filter(status='pending')  # Отримуємо надіслані запити

        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            friend = None

            # Шукаємо користувача за телефоном або email
            try:
                if "@" in identifier:
                    friend = CustomUser.objects.get(email=identifier)
                else:
                    friend = CustomUser.objects.get(phone_number=identifier)
            except CustomUser.DoesNotExist:
                form.add_error('identifier', 'Користувача з такою інформацією не знайдено.')

            if friend:
                # Перевіряємо, чи не намагається користувач надіслати запит самому собі
                if friend == request.user:
                    form.add_error('identifier', 'Ви не можете надіслати запит самому собі.')
                else:
                    # Шукаємо існуючий запит на дружбу
                    friend_request, created = FriendRequest.objects.get_or_create(from_user=request.user,
                                                                                  to_user=friend)

                    if created:
                        messages.success(request, 'Запит на додавання в друзі успішно надісланий!')
                    elif friend_request.status in ['rejected', 'accepted']:
                        # Якщо запит був прийнятий або відхилений, дозволяємо надіслати його знову
                        friend_request.status = 'pending'  # Оновлюємо статус
                        friend_request.save()
                        messages.success(request, 'Запит на дружбу повторно надісланий!')
                    else:
                        messages.warning(request, 'Запит вже був надісланий.')

                    return redirect('friends_list')

        # У разі помилки, залишаємо форму та відображаємо запити
        return render(request, self.template_name, {
            'form': form,
            'friends': friends,
            'friend_requests': friend_requests,
            'sent_requests': sent_requests,
        })


@login_required(login_url='/login/')
def delete_friend(request, friend_id):
    if request.method == "POST":
        friend = get_object_or_404(CustomUser, id=friend_id)
        request.user.friends.remove(friend)  # Видаляємо друга зі списку друзів
        return redirect('friends_list')


@login_required(login_url='/login/')
def handle_friend_request(request, request_id):
    # Шукаємо запит на дружбу
    friend_request = get_object_or_404(FriendRequest, id=request_id)

    # Перевіряємо, чи користувач є тим, хто надіслав або отримав запит
    if friend_request.to_user == request.user:
        # Обробляємо прийняття або відхилення запиту
        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'accept':
                # Додаємо у друзі
                request.user.friends.add(friend_request.from_user)
                friend_request.from_user.friends.add(request.user)
                friend_request.status = 'accepted'
                messages.success(request, 'Запит прийнято, користувач доданий у друзі.')
            elif action == 'reject':
                friend_request.status = 'rejected'
                messages.info(request, 'Запит відхилено.')

            friend_request.save()
    elif friend_request.from_user == request.user:
        # Скасовуємо запит
        if request.method == 'POST':
            friend_request.delete()
            messages.success(request, 'Запит на дружбу скасовано.')

    return redirect('friends_list')


@login_required(login_url='/login/')
def create_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.user in project.users.all():
        return redirect('home')

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project  # Призначити проект
            task.save()  # Зберегти завдання без призначення користувача
            return redirect('project_detail', pk=project.pk)  # Перенаправлення на деталі проекту
    else:
        form = TaskForm()

    return render(request, 'tasks_html/create_task.html', {'form': form, 'project': project})


class EditTaskView(LoginRequiredMixin, View):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

        # Перевірка прав користувача
        if request.user in task.project.users.all():
            return redirect('home')

        form = EditTaskForm(instance=task)
        context = {
            'form': form,
            'task': task,
        }
        return render(request, 'tasks_html/edit_task.html', context)

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = EditTaskForm(request.POST, request.FILES, instance=task)

        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=task.project.id)

        context = {
            'form': form,
            'task': task,
        }
        return render(request, 'tasks_html/edit_task.html', context)


@login_required(login_url='/login/')
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        # Обробка взяття завдання
        if 'task_id' in request.POST:
            task.assigned_user = request.user
            task.work_status = 'in_process'
            task.save()
            return redirect('task_detail', task_id=task.id)

        # Видалення коментаря
        if 'delete_comment_id' in request.POST:
            comment_id = request.POST.get('delete_comment_id')
            comment = get_object_or_404(Comment, id=comment_id)

            # Перевіряємо, чи користувач є автором коментаря
            if comment.user == request.user:
                comment.delete()
                return redirect('task_detail', task_id=task.id)

        # Лайк коментаря
        if 'like_comment_id' in request.POST:
            comment_id = request.POST.get('like_comment_id')
            comment = get_object_or_404(Comment, id=comment_id)

            # Лайкаємо тільки чужі коментарі
            if comment.user != request.user:
                if comment.likes < 1:  # Якщо лайків ще не було
                    comment.likes += 1
                else:  # Якщо лайк вже існує, видаляємо
                    comment.likes -= 1

                comment.save()
                return redirect('task_detail', task_id=task.id)

        # Додавання нового коментаря
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user  # Встановлюємо поточного користувача як автора
            comment.created_at = timezone.now()
            comment.save()
            return redirect('task_detail', task_id=task.id)
    else:
        form = CommentForm()

    # Отримуємо коментарі, пов'язані із завданням
    comments = Comment.objects.filter(task=task).order_by('-created_at')

    return render(request, 'tasks_html/task_detail.html', {
        'task': task,
        'comments': comments,
        'form': form  # Передаємо форму в шаблон
    })


@login_required(login_url='/login/')
def cancel_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        # Відмінити призначення користувача
        task.assigned_user = None
        task.work_status = 'free'
        task.save()
        return redirect('project_detail', pk=task.project.id)  # Перенаправлення на деталі проекту

    return redirect('task_detail', task_id=task.id)


from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatRoom, Profile
from .forms import ChatEditForm, ChatCreateForm, ProfileEditForm
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.utils.text import slugify

User = get_user_model()


class ChatRoomListView(LoginRequiredMixin, ListView):
    template_name = 'chat/lobby.html'
    model = ChatRoom
    paginate_by = 10
    queryset = ChatRoom.objects.filter(chat_type=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chat_rooms'] = ChatRoom.objects.all()
        return context


class PrivateChatListView(LoginRequiredMixin, ListView):
    template_name = 'user/private_chat_list.html'
    model = ChatRoom
    paginate_by = 5

    def get_queryset(self):
        qs = ChatRoom.objects.filter(
            chat_type=1, participants=self.request.user
        )
        return qs


@login_required
def chat_room_view(request, chat_name):
    chat_room = get_object_or_404(ChatRoom, slug=chat_name)
    if chat_room.chat_type == 1:
        return HttpResponseForbidden()
    if request.method == 'GET':
        is_participant = request.user in chat_room.participants.all()
        is_banned = request.user in chat_room.black_list.all()
        is_moderator = (request.user == chat_room.owner) or\
                       (request.user in chat_room.moderators.all())
        return render(request, 'chat/room.html',
                      {'chat_room': chat_room,
                       'is_participant': is_participant,
                       'is_banned': is_banned,
                       'is_moderator': is_moderator})
    else:
        if 'join' in request.POST:
            chat_room.participants.add(request.user)
            chat_room.save()
        return redirect('chat:chat_room', chat_name=chat_name)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('chat:lobby')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration.html', {'form': form})


@login_required
def chat_room_settings_view(request, chat_name):
    chat_room = get_object_or_404(ChatRoom, slug=chat_name)
    if request.method == 'POST':
        if 'delete' in request.POST:
            return redirect('chat:delete_confirm', chat_name=chat_room.slug)
        form = ChatEditForm(request.POST)
        if form.is_valid():
            black_list = form.cleaned_data.get('black_list')
            moderators_list = form.cleaned_data.get('moderators_list')
            chat_room.black_list.set(black_list)
            chat_room.moderators.set(moderators_list)
            chat_room.save()
            return redirect('chat:chat_room', chat_name=chat_name)
    else:
        form = ChatEditForm(initial={
            'black_list': chat_room.black_list.all(),
            'moderators_list': chat_room.moderators.all()
        })
        # we don't want all of the registered users to show up in the form
        qs_m = chat_room.moderators.all()
        qs_b = chat_room.black_list.all()
        form.fields['black_list'].queryset = qs_b.distinct()
        form.fields['moderators_list'].queryset = qs_m.distinct()
    return render(request, 'chat/edit.html',
                  {'form': form,
                   'chat_room': chat_room})


@login_required
def chat_participant_view(request, chat_name, username):
    chat_room = get_object_or_404(ChatRoom, slug=chat_name)
    user = get_object_or_404(User, username=username)
    if request.user == chat_room.owner or \
       request.user in chat_room.moderators.all():
        if request.method == 'GET':
            is_banned = user in chat_room.black_list.all()
            messages = user.sent_messages.filter(
                chat_room=chat_room
            ).order_by('-timestamp')[0:5:-1]
            messages_count = user.sent_messages.filter(
                chat_room=chat_room
            ).count()
            is_moderator = (user == chat_room.owner) or \
                           (user in chat_room.moderators.all())

            return render(request, 'chat/participant.html',
                          {'chat_room': chat_room,
                           'user': user,
                           'messages': messages,
                           'messages_count': messages_count,
                           'is_banned': is_banned,
                           'is_moderator': is_moderator})
        else:
            if 'unban' in request.POST:
                chat_room.black_list.remove(user)
                chat_room.save()
            elif 'ban' in request.POST:
                chat_room.black_list.add(user)
                chat_room.save()
            elif 'mod' in request.POST:
                chat_room.moderators.add(user)
                chat_room.save()
            elif 'unmod' in request.POST:
                chat_room.moderators.remove(user)
                chat_room.save()

            return redirect('chat:participant',
                            chat_name=chat_name,
                            username=username)

    else:
        return HttpResponseForbidden()


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    # determine whether the requested profile belongs to the user
    is_request_user = user == request.user
    # determine whether the profile belongs to one of the user's friends
    is_friend = profile in request.user.profile.friends.all()
    is_desired_friend =\
        profile in request.user.profile.outcoming_requests.all()
    desires_to_be_a_friend =\
        profile in request.user.profile.incoming_requests.all()
    if request.method == 'GET':
        return render(request, 'user/profile.html',
                      {'profile': profile,
                       'user': user,
                       'is_request_user': is_request_user,
                       'is_friend': is_friend,
                       'is_desired_friend': is_desired_friend,
                       'desires_to_be_a_friend': desires_to_be_a_friend
                       })
    else:
        if 'add_friend' in request.POST:
            request_profile = request.user.profile
            request_profile.outcoming_requests.add(profile)
            request_profile.save()

        elif 'remove_friend' in request.POST:
            request_profile = request.user.profile
            request_profile.friends.remove(profile)
            request_profile.save()

        elif 'accept_friend' in request.POST:
            user_to_accept = get_object_or_404(
                User, username=request.POST['person']
            )
            profile_to_accept = user_to_accept.profile
            profile_to_accept.outcoming_requests.remove(profile)
            profile.outcoming_requests.remove(profile_to_accept)
            profile.friends.add(profile_to_accept)

        elif 'decline_friend' in request.POST:
            user_to_decline = get_object_or_404(
                User, username=request.POST['person']
            )
            profile_to_decline = user_to_decline.profile
            profile_to_decline.outcoming_requests.remove(profile)
            profile.outcoming_requests.remove(profile_to_decline)

        elif 'chat' in request.POST:
            return redirect('chat:private_chat', username=username)

        elif 'edit' in request.POST:
            return redirect('chat:profile_edit', username=username)

        return redirect('chat:profile',
                        username=username)


@login_required
def create_chat_room_view(request):
    if request.method == 'POST':
        form = ChatCreateForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            name = cd.get('name')
            slug = cd.get('slug')
            owner = request.user
            chat_room = ChatRoom.objects.create(
                name=name, slug=slug, owner=owner
            )
            chat_room.participants.add(request.user)
            return redirect('chat:chat_room', slug)

    else:
        if request.user.owned_chats.all().count() < 3\
                or request.user.is_staff:
            form = ChatCreateForm()
        else:
            return render(request, 'chat/create.html',
                          {'denied': True})
    return render(request, 'chat/create.html',
                  {'form': form})


@login_required
def delete_confirm_view(request, chat_name):
    chat_room = get_object_or_404(ChatRoom, slug=chat_name)
    if request.method == 'POST':
        if chat_room.owner == request.user:
            chat_room.delete()
        return redirect('chat:lobby')
    else:
        return render(request, 'chat/delete_confirm.html',
                      {'chat_room': chat_room})


@login_required
def edit_profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if 'first_name' in cd:
                user.first_name = cd['first_name']
            if 'last_name' in cd:
                user.last_name = cd['last_name']
            if 'email' in cd:
                user.email = cd['email']
            if 'date_of_birth' in cd:
                profile.date_of_birth = cd['date_of_birth']
            user.save()
            profile.save()
            return redirect('chat:profile', username=username)
    else:
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'date_of_birth': profile.date_of_birth,
        }
        form = ProfileEditForm(initial=initial)
    return render(request, 'user/edit.html',
                  {'form': form,
                   'user': user})


@login_required
def private_chat_view(request, username):
    user1 = request.user
    user2 = get_object_or_404(User, username=username)
    chat_name_string1 = f'Private Chat {user1.username}-{user2.username}'
    chat_name_string2 = f'Private Chat {user2.username}-{user1.username}'
    qs1 = ChatRoom.objects.filter(chat_type=1, name=chat_name_string1)
    qs2 = ChatRoom.objects.filter(chat_type=1, name=chat_name_string2)
    qs = qs1 | qs2
    if not qs.exists():
        chat_room = ChatRoom.objects.create(
            name=chat_name_string1, slug=slugify(chat_name_string1),
            chat_type=1
        )
        chat_room.save()
        chat_room.participants.add(user1, user2)
        chat_room.save()
    else:
        chat_room = qs[0]
    return render(request, 'user/private_chat.html',
                  {'chat_room': chat_room,
                   'companion': user2})

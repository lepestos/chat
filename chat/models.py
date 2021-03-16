from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Message(models.Model):
    author = models.ForeignKey(User, related_name='sent_messages',
                               on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)  # timestamp of creation
    chat_room = models.ForeignKey('ChatRoom',
                                  related_name='messages',
                                  on_delete=models.CASCADE,
                                  null=True)
    is_read = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.author.username}: {self.content}'

    class Meta:
        ordering = ['timestamp']

    @staticmethod
    def last_10_messages(chat_room, order):
        """
        loading messages for a specific chat room
        """
        return Message.objects.filter(chat_room=chat_room)\
            .order_by('-timestamp')[order*10:order*10+10]

    def read(self):
        self.is_read = True
        self.save()


class ChatRoom(models.Model):
    # 'superuser' of the chat room
    owner = models.ForeignKey(User, related_name='owned_chats',
                              on_delete=models.CASCADE, blank=True,
                              null=True)
    name = models.CharField(max_length=64)
    date_created = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=64, db_index=True)
    participants = models.ManyToManyField(User,
                                          related_name='participant_at',
                                          blank=True)
    black_list = models.ManyToManyField(User,
                                        related_name='banned_from',
                                        blank=True)
    moderators = models.ManyToManyField(User,
                                        related_name='moderator_at',
                                        blank=True)

    chat_types = [
        (0, 'public_chat'),
        (1, 'private_chat')
    ]
    chat_type = models.IntegerField(choices=chat_types, default=0)

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.chat_type == 1:
            return f'{self.messages.last()}'
        return f'{self.name}'


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile',
                                on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    friends = models.ManyToManyField('self', blank=True)
    # friend requests
    outcoming_requests = models.ManyToManyField('self', blank=True,
                                                related_name=
                                                'incoming_requests',
                                                symmetrical=False)

    def __str__(self):
        return f'Profile for user {self.user.username}'


class PrivateMessage(models.Model):
    sender = models.OneToOneField(User,
                                  related_name='private_messages_sent',
                                  on_delete=models.CASCADE)
    recipient = models.OneToOneField(User,
                                     related_name='private_messages_received',
                                     on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author.username}: {self.content}'

    @staticmethod
    def last_10_messages(chat_room, order):
        """
        loading messages for a specific chat room
        """
        return Message.objects.filter(chat_room=chat_room)\
            .order_by('-timestamp')[order * 10:order * 10 + 10]

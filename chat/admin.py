from django.contrib import admin
from .models import Message, ChatRoom, Profile


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    ordering = ['-timestamp']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

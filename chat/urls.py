from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'chat'


urlpatterns = [
    path('', views.ChatRoomListView.as_view(), name='lobby'),
    path('chat/<slug:chat_name>/', views.chat_room_view,
         name='chat_room'),
    path('register/', views.register_view, name='registration'),
    path('accounts/login/', auth_views.LoginView.as_view(),
         name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(),
         name='logout'),
    path('chat/<slug:chat_name>/edit/', views.chat_room_settings_view,
         name='chat_room_settings'),
    path('chat/<slug:chat_name>/user/<str:username>/',
         views.chat_participant_view, name='participant'),
    path('profile/<str:username>/', views.profile_view,
         name='profile'),
    path('create/', views.create_chat_room_view, name='chat_room_create'),
    path('<slug:chat_name>/delete/', views.delete_confirm_view,
         name='delete_confirm'),
    path('profile/<str:username>/edit/', views.edit_profile_view,
         name='profile_edit'),
    path('message/<str:username>/', views.private_chat_view,
         name='private_chat'),
    path('messages/', views.PrivateChatListView.as_view(),
         name='private_chat_list'),
]

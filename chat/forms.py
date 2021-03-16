from django import forms
from django.contrib.auth import get_user_model
from .models import ChatRoom, Profile

User = get_user_model()


class ChatEditForm(forms.Form):
    black_list = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    moderators_list = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )


class ChatCreateForm(forms.ModelForm):
    class Meta:
        model = ChatRoom
        fields = ('name', 'slug',)


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=64, required=False)
    last_name = forms.CharField(max_length=64, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Profile
        fields = ('date_of_birth',)

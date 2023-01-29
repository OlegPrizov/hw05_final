from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Чем вы хотите поделиться?',
            'group': 'К какой группе относится ваш пост?',
            'image': 'Добавьте фотографию'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Оставьте комментарий',
        }
        help_texts = {
            'text': 'Оставьте комментарий help_texts',
        }

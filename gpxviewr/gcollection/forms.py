from django import forms

from gcollection.models import GCollection, GUser, GcollectionShare


class GCollectionForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        queryset=GUser.objects.none(),
    )
    name = forms.CharField(
        widget=forms.widgets.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'minlength': '3'})
    )
    date = forms.DateField(
        widget=forms.widgets.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['user'].queryset = GUser.objects.all().filter(pk=user.pk)

    class Meta:
        model = GCollection
        fields = ['user', 'name', 'date',]


class GcollectionShareForm(forms.ModelForm):
    perm_download = forms.BooleanField(widget=forms.widgets.CheckboxInput())
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['gcollection'].queryset = GCollection.objects.all().filter(user=user)

    class Meta:
        model = GcollectionShare
        fields = ['gcollection', 'valid_until_date', 'perm_download',]


class GCollectionProfileDeleteForm(forms.Form):
    user_id = forms.CharField(required=True)

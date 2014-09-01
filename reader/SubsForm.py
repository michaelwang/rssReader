from django import forms
from django.utils.translation import ugettext_lazy as _

class SubsForm(forms.Form):
      folder_id = forms.IntegerField( required = False  ) 
      feed_id = forms.IntegerField( min_value = 0 )

class RegistrationForm(forms.Form):
      email = forms.EmailField(label=_("E-mail"))
      password1 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
      password2 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password (again)"))
      username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                  max_length=30,
                                  label=_("Username"),
                                  error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})

      def clean(self):
          """
          Verifiy that the values entered into the two password fields
          match. Note that an error here will end up in
          ``non_field_errors()`` because it doesn't apply to a single
          field.
        
          """
          if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
             if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError("The two password fields didn't match.")
          return self.cleaned_data      

class BeforeRegister(forms.Form):
      email = forms.EmailField(label = _("E-mail"))

class LoginForm(forms.Form):
      username = forms.EmailField(label=_("E-mail"))
      password = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
      

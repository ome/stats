#!/usr/bin/env python
# 
# 
# 
# Copyright (c) 2009 University of Dundee. 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
# 
# Version: 1.0
#

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm

from omero_qa.qa.models import UserComment, Trac, TestEngineResult, \
    Feedback, FeedbackStatus, FileFormat

### FORMS ###

class UserForm(ModelForm):

    password = forms.CharField(max_length=20, widget=forms.PasswordInput(attrs={'size':20}))
    confirmation = forms.CharField(max_length=20, widget=forms.PasswordInput(attrs={'size':20}))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        

    def clean_username(self):
        try:
            user = User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        else:
            raise forms.ValidationError('This username already exist.')
            
    def clean_email(self):
        if len(self.cleaned_data['email']) < 5:
             raise forms.ValidationError('This is not a valid email address.')
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError('This email already exist.')
            
    def clean_confirmation(self):
        if self.cleaned_data['password'] or self.cleaned_data['confirmation']:
            if len(self.cleaned_data['password']) < 3:
                raise forms.ValidationError('Password must be between 3 and 20 letters long')
            if len(self.cleaned_data['password']) > 20:
                raise forms.ValidationError('Password must be between 3 and 20 letters long')
            if self.cleaned_data['password'] != self.cleaned_data['confirmation']:
                raise forms.ValidationError('Passwords do not match')
            else:
                return self.cleaned_data['password']


class FeedbackForm(ModelForm):

    class Meta:
        model = Feedback
        fields = ('app_name', 'app_version', 'java_version', 'java_classpath', 'python_version', \
                'python_classpath', 'os_name', 'os_arch', 'os_version', 'user_agent', 'extra', 'error', 'comment', \
                'ticket', 'test_files', 'user', 'email', 'token', 'selected_file')


class TestEngineResultForm(ModelForm):

    class Meta:
        model = TestEngineResult
        fields = ('started', 'ended', 'error', 'repo_java_version', 'repo_java_classpath', \
                'repo_python_version', 'repo_python_classpath', 'repo_os_name', 'repo_os_arch', 'repo_os_version', 'support_level')


#class AdditionalFileForm(ModelForm):
#
#    class Meta:
#        model = Feedback
#        fields = ('file_path', 'file_name', 'file_size')


class StatusForm(forms.Form):
    
    status = forms.ModelChoiceField(queryset=FeedbackStatus.objects.all(), empty_label=None)
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}), required=False)


class TicketForm(ModelForm):
    
    owner = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True, is_superuser=False).exclude(username='test_engine'))
    cc = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'size':70}), required=False)
    summary = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'size':70}))
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 60}))
    
    class Meta:
        model = Trac
        exclude = ('ticket')


class ExistingTicketForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ExistingTicketForm, self).__init__(*args, **kwargs)
        try:
            self.fid = long(kwargs['initial']['fid'])
        except:
            self.fid = None
        
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 7, 'cols': 50}))
    
    class Meta:
        model = Trac
    
    def clean_ticket(self):
        system = self.data.get('system')
        ticket = self.cleaned_data['ticket']
        if self.fid is None:
            raise forms.ValidationError(u'Select a valid feedback.')
        try:
            feedback = Feedback.objects.get(pk=self.fid, ticket__system__exact=system, ticket__ticket__exact=ticket)
        except Feedback.DoesNotExist:
            return ticket
        else:
            raise forms.ValidationError(u'Ticket %s was already added to feedback %s.' % (ticket, self.fid))

class CommentForm(forms.Form):
    
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 7, 'cols': 50}), required=False)


class UserCommentForm(ModelForm):
    
    email = forms.EmailField(max_length=100, required=False, widget=forms.TextInput(attrs={'size':45}), label="Your email")
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 7, 'cols': 50}))
    
    class Meta:
        model = UserComment
        exclude = ('creation_date', 'user', 'email') #'comment', 


class LoginForm(forms.Form):
    
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'size':10}))
    password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={'size':10}))


class FileTypeForm(forms.Form):

    file_format = forms.ModelChoiceField(queryset=FileFormat.objects.all(),  widget=forms.Select(attrs={'onchange':'window.location.href=\'?file_format=\'+this.options[this.selectedIndex].value'}))


class EmailForm(forms.Form):

    email = forms.EmailField(max_length=100, widget=forms.TextInput(attrs={'size':32, 'onchange':'javascript:saveEmail(this.value);'}), required=False)


class UploadFileForm(forms.Form):
    
    Filedata  = forms.FileField(required=False)

    def clean_Filedata(self):
        if self.cleaned_data['Filedata'] is None:
            raise forms.ValidationError('This field is required.')
        if self.cleaned_data['Filedata'].size > 2000000000:
            raise forms.ValidationError('Photo size file cannot be greater them 10MB.')


class FilterFeedbackForm(forms.Form):
    
    status = forms.ModelChoiceField(queryset=FeedbackStatus.objects.all(), empty_label="all", required=False)
    date = forms.DateTimeField(required=False)
    text = forms.CharField(max_length=250, widget=forms.TextInput(), required=False)
    useremail = forms.CharField(max_length=250, widget=forms.TextInput(), required=False, label="User/email")

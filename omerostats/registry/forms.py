#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#
# Copyright (c) 2009-2013 University of Dundee.
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


class UserForm(ModelForm):

    password = forms.CharField(
        max_length=20,
        widget=forms.PasswordInput(attrs={'size': 20}))
    confirmation = forms.CharField(
        max_length=20,
        widget=forms.PasswordInput(attrs={'size': 20}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_username(self):
        try:
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        else:
            raise forms.ValidationError('This username already exist.')

    def clean_email(self):
        if len(self.cleaned_data['email']) < 5:
            raise forms.ValidationError('This is not a valid email address.')
        try:
            User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError('This email already exist.')

    def clean_confirmation(self):
        if self.cleaned_data['password'] or self.cleaned_data['confirmation']:
            if len(self.cleaned_data['password']) < 3:
                raise forms.ValidationError(
                    'Password must be between 3 and 20 letters long')
            if len(self.cleaned_data['password']) > 20:
                raise forms.ValidationError(
                    'Password must be between 3 and 20 letters long')
            if (self.cleaned_data['password'] !=
                    self.cleaned_data['confirmation']):
                raise forms.ValidationError('Passwords do not match')
            else:
                return self.cleaned_data['password']


class LoginForm(forms.Form):

    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'size': 10}))
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={'size': 10}))

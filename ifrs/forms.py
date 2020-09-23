import os
import re
from datetime import datetime
from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from ifrs.funcs import get_dates_for_choice_field


class UploadForm(forms.Form):
    upload_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file_field',
            'id': 'file_field', }),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data:
            file = cleaned_data['upload_file']
            if file:
                file_type = file.content_type.split('/')[1]
                file_name, file_extension = os.path.splitext(file.name)
                if file_type in settings.UPLOAD_FILE_TYPES and file_extension in settings.UPLOAD_FILE_EXTENSIONS:
                    patterns = settings.UPLOAD_FILE_NAMES
                    for pattern in patterns:
                        match = re.fullmatch(pattern, file_name)
                        if match:
                            break
                    else:
                        raise forms.ValidationError('The chosen file has invalid filename.')
                    file_date = datetime.strptime(file_name.split(' ')[1], '%d.%m.%Y')
                    max_date = datetime(datetime.now().year, datetime.now().month, 1)
                    if file_date > max_date:
                        max_date = max_date.strftime('%d.%m.%Y')
                        raise forms.ValidationError(f'The chosen file has invalid date. Max date: {max_date}.')
                    if file.size > settings.MAX_UPLOAD_SIZE:
                        raise forms.ValidationError(
                            f'File size should be less than {filesizeformat(settings.MAX_UPLOAD_SIZE)} '
                            f'(current: {filesizeformat(file.size)}).'
                        )
                else:
                    raise forms.ValidationError('File type is not supported.')
            else:
                raise forms.ValidationError('No file chosen.')
            return cleaned_data


class DateChoiceForm(forms.Form):
    ifrs_comp = forms.ChoiceField(
        choices=((None, '-'), ('all', 'All'), ('pd', 'PD'), ('lgd', 'LGD'), ('ccf', 'CCF')),
        widget=forms.Select(attrs={
            'class': 'select_field', }),
        label='IFRS component',
    )

    def __init__(self, *args, **kwargs):
        super(DateChoiceForm, self).__init__(*args, **kwargs)
        self.fields['date'] = forms.ChoiceField(
            choices=get_dates_for_choice_field(),
            widget=forms.Select(attrs={
                'class': 'select_field',
                }),
            label='Report date',
        )

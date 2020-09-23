from datetime import datetime
from ifrs.models import IFRSData
from django.contrib import messages
from django.shortcuts import (render,
                              redirect, )


def ifrs_page(request):
    if request.method == 'GET':
        ifrs_data = IFRSData.objects.filter().all().order_by('date')
        return render(request, 'ifrs_page.html', {'ifrs_data': ifrs_data})
    elif request.method == 'POST':
        delete_date = request.POST.get('del_ifrs')
        date = datetime.strptime(delete_date, '%d.%m.%Y').date()
        IFRSData.objects.filter(date=date).delete()
        message = f'IFRS data on {delete_date} successfully deleted.'
        messages.add_message(request, messages.SUCCESS, message)
        return redirect('ifrs_page')

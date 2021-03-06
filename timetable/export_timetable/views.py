# -*- coding:utf-8 -*-
import os
import xlwt
import tempfile
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.http import HttpResponse, HttpResponseRedirect

from .export_xls import TimeTable



class ExportXLS(TemplateView):
    template_name = "export.html"
    error_msg = u"아이디와 비밀번호를 체크해주세요."

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        std_id = request.POST['student_id']
        password = request.POST['password']
        
        t = TimeTable()
        t.login(std_id, password)

        if not t.is_login:
            return render(request, self.template_name, {'error_msg':self.error_msg})

        table_data = t.export()

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet(u'시간표')

        algn = xlwt.Alignment()
        algn.wrap = 1
        style = xlwt.XFStyle()
        style.alignment = algn

        fields = [u'교시',u'월요일',u'화요일',u'수요일',u'목요일',u'금요일',u'토요일']

        for i, field in enumerate(fields):
            worksheet.write(0,i, unicode(field))

        for i, data in enumerate(table_data['table_data']):
            for j in range(len(data)):
                if data[table_data['key_data'][j]] is not None:
                    worksheet.write(i+1, j, unicode(data[table_data['key_data'][j]].replace(',','\n')), style)

        fd, fn = tempfile.mkstemp()
        os.close(fd)
        workbook.save(fn)
        fh = open(fn, 'rb')
        resp = fh.read()
        fh.close()

        response = HttpResponse(resp, mimetype='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.xls' % \
            (t.STUDENT_ID,)
        return response


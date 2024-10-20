from django.contrib import admin
from .models import *

admin.site.register(Book)
admin.site.register(Student)
admin.site.register(IssuedBook)
admin.site.register(BookRequest)
admin.site.register(ContactMessage)
admin.site.register(Payment)

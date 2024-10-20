from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView




urlpatterns = [
    path("", views.index, name="index"),
    path("add_book/", views.add_book, name="add_book"),
    path("view_books/", views.view_books, name="view_books"),
    path("view_students/", views.view_students, name="view_students"),
    path("issue_book/", views.issue_book, name="issue_book"),
    path('issued_books/', views.view_issued_book, name='view_issued_book'),
    path('delete_issue/<int:book_id>/', views.delete_issued_book, name='delete_issued_book'),
    path("student_issued_books/", views.student_issued_books, name="student_issued_books"),
    path("profile/", views.profile, name="profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path("student_registration/", views.student_registration, name="student_registration"),
    path("change_password/", views.change_password, name="change_password"),
    path("student_login/", views.student_login, name="student_login"),
    path("admin_login/", views.admin_login, name="admin_login"),
    path("logout/", views.Logout, name="logout"),
    path("delete_book/<int:myid>/", views.delete_book, name="delete_book"),
    path("delete_student/<int:myid>/", views.delete_student, name="delete_student"),
    path("books/", views.view_all_books, name="view_all_books"),
    path("request_book/<int:book_id>/", views.request_book, name="request_book"),
    path("manage_requests/", views.manage_requests, name="manage_requests"),
    path("approve_request/<int:request_id>/", views.approve_request, name="approve_request"),
    path("deny_request/<int:request_id>/", views.deny_request, name="deny_request"),
    path('update_request/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('book/<int:book_id>/', views.book_details, name='book_details'),
    path('contact/', views.contact, name='contact'),


    path('contact-messages/', views.view_contact_messages, name='view_contact_messages'),
    path('contact-messages/<int:message_id>/', views.contact_message_detail, name='contact_message_detail'),

     path('payment/<int:book_request_id>/', views.payment_view, name='payment_view'),
     path('payment/success/', views.payment_successfull, name='payment_success'),  # Add a success page


     path('payments/', views.view_payments, name='view_payments'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

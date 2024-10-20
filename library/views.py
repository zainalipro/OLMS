from library.forms import IssueBookForm
from django.shortcuts import redirect, render,HttpResponse , get_object_or_404
from .models import *
from .forms import IssueBookForm
from django.contrib.auth import authenticate, login, logout
from . import forms, models
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse



def index(request):
    return render(request, "index.html")

@login_required(login_url='/admin_login')
def add_book(request):
    if request.method == "POST":
        name = request.POST['name']
        author = request.POST['author']
        isbn = request.POST['isbn']
        category = request.POST['category']
        price = request.POST['price']  # New line to get the price
        
        # Handle file uploads
        cover_image = request.FILES.get('cover_image')
        pdf_file = request.FILES.get('pdf_file')

        # Create the book instance
        book = Book.objects.create(
            name=name,
            author=author,
            isbn=isbn,
            category=category,
            cover_image=cover_image,
            pdf_file=pdf_file,
            price=price  # Include price in the creation
        )

        alert = True
        return render(request, "add_book.html", {'alert': alert})
    return render(request, "add_book.html")



@login_required(login_url = '/admin_login')
def view_books(request):
    books = Book.objects.all()
    return render(request, "view_books.html", {'books':books})

@login_required(login_url = '/admin_login')
def view_students(request):
    students = Student.objects.all()
    return render(request, "view_students.html", {'students':students})

from django.core.mail import send_mail
from django.conf import settings

@login_required(login_url='/admin_login')
def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            student_id = request.POST['name2']
            isbn = request.POST['isbn2']

            # Check if the book is already issued to the student
            # existing_issue = models.IssuedBook.objects.filter(student_id=student_id, isbn=isbn).exists()
            # if existing_issue:
            #     alert = False
            #     error_message = "This book has already been issued to the student."
            #     return render(request, "issue_book.html", {'form': form, 'alert': alert, 'error_message': error_message})

            # Create and save the new issued book record
            obj = models.IssuedBook()
            obj.student_id = student_id
            obj.isbn = isbn
            obj.save()

            # Get student email to send notification
            student = models.Student.objects.get(user_id=student_id)

            # Send email notification
            subject = 'Book Issued Notification'
            message = f'Dear {student.user.get_full_name()},\n\nThe book "{obj.isbn}" has been issued to you. Please check your account for further details.\n\nThank you!'
            email_from = settings.DEFAULT_FROM_EMAIL
            recipient_list = [student.user.email]

            send_mail(subject, message, email_from, recipient_list)

            alert = True
            return render(request, "issue_book.html", {'obj': obj, 'alert': alert})

    return render(request, "issue_book.html", {'form': form})





@login_required(login_url='/admin_login')
def view_issued_book(request):
    issued_books = IssuedBook.objects.all()
    details = []

    for issued in issued_books:
        days = (date.today() - issued.issued_date).days
        fine = max(0, (days - 14) * 5)  # Fine calculation
        
        # Fetch the book and student associated with the issued book
        book = models.Book.objects.filter(isbn=issued.isbn).first()  # Using .first() instead of list to avoid IndexError
        student = models.Student.objects.filter(user=issued.student_id).first()
        
        # Check if both book and student exist to avoid NoneType issues
        if book and student:
            detail = (student.user, student.user_id, book.name, book.isbn, issued.issued_date, issued.expiry_date, fine, book.id)
            details.append(detail)

    return render(request, "view_issued_book.html", {'issuedBooks': issued_books, 'details': details})


@login_required(login_url='/admin_login')
def delete_issued_book(request, book_id):
    issued_book = get_object_or_404(IssuedBook, id=book_id)

    if request.method == 'POST':
        issued_book.delete()
        return redirect('view_issued_book')  # Redirect to the issued books list

    return render(request, 'confirm_delete.html', {'issued_book': issued_book})
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Payment

@login_required(login_url='/admin_login')
def view_payments(request):
    payments = Payment.objects.all()  # Get all payments
    total_payments = sum(payment.book_price for payment in payments)  # Calculate total payments

    return render(request, 'admin_payments.html', {
        'payments': payments,
        'total_payments': total_payments,
    })



@login_required(login_url='/student_login')
def student_issued_books(request):
    student = Student.objects.filter(user_id=request.user.id).first()
    
    # Get all issued books for the student
    issued_books = IssuedBook.objects.filter(student_id=student.user.id)

    # Implement search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        # Get the list of book ISBNs that match the search query
        matching_books = Book.objects.filter(name__icontains=search_query)
        # Filter issued_books based on those matching ISBNs
        issued_books = issued_books.filter(isbn__in=matching_books.values_list('isbn', flat=True))

    li = []  # Consolidated list to hold book details and issued info

    for issued_book in issued_books:
        # Use the ISBN to get the related Book object
        book = get_object_or_404(Book, isbn=issued_book.isbn)
        
        days = (timezone.now().date() - issued_book.issued_date).days
        fine = max(0, (days - 14) * 5)
        is_expired = issued_book.expiry_date < timezone.now().date()

        li.append({
            'student_id': student.user.id,
            'student_name': student.user.get_full_name(),
            'book_name': book.name,
            'author': book.author,
            'book_id': book.id,
            'issued_date': issued_book.issued_date,
            'expiry_date': issued_book.expiry_date,
            'fine': fine,
            'is_expired': is_expired
        })
        print(f"is_expired -- {is_expired}")
        if is_expired:
            book_request = BookRequest.objects.filter(student=student, book=book).first()
            if book_request:
                print(f"Current BookRequest status: {book_request.status}")  # Print current status
                if book_request.status.lower() == 'approved':  # Check status case-insensitively
                    print("Changing status to request")
                    book_request.status = 'request'
                    book_request.save()
                    print(f"New BookRequest status: {book_request.status}")  # Confirm change
                else:
                    print("BookRequest is not approved, current status:", book_request.status)
            else:
                print("No BookRequest found for this student and book.")
        
        

    return render(request, 'student_issued_books.html', {
        'li': li,
        'search_query': search_query,
    })








# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BookRequest

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import BookRequest, Payment
from datetime import datetime
@login_required(login_url='/student_login')
def payment_view(request, book_request_id):
    book_request = get_object_or_404(BookRequest, id=book_request_id)

    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        expiry_date_str = request.POST.get('expiry_date')  # Format: YYYY-MM-DD
        cvv = request.POST.get('cvv')

        # Validate the card expiry date
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        if expiry_date <= datetime.today().date():
            messages.error(request, "Your card has expired. Please use a valid card.")
            return render(request, 'payment.html', {'book_request': book_request})

        # Create the payment
        payment = Payment.create_payment(book_request, card_number, expiry_date, cvv)

        # Update the book request status to 'Approved'
        book_request.status = 'approved'
        book_request.save()

        # Create an IssuedBook record using existing fields
        issued_book = IssuedBook()
        issued_book.student_id = book_request.student.user.id  # Assuming this is how you get the student ID
        issued_book.isbn = book_request.book.isbn
        issued_book.save()

        # Notify the user
        messages.success(request, f"Payment successful! The book '{book_request.book.name}' has been issued to you for 14 days.")

        # Send confirmation email
        subject = 'Book Issued Confirmation'
        message = (
            f"Dear {book_request.student.user.get_full_name()},\n\n"
            f"Your payment for the book '{book_request.book.name}' has been processed successfully.\n"
            f"The book has been issued to you for 14 days.\n\n"
            "Thank you for using our library management system!\n"
            "Best regards,\n"
            "Library Management Team"
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [book_request.student.user.email]

        send_mail(subject, message, from_email, recipient_list)

        # Redirect to a success page or the books list
        return redirect('payment_success')  # Replace with your success URL

    return render(request, 'payment.html', {'book_request': book_request})



def payment_successfull(request):
    return render(request , 'payment_successfull.html')






@login_required(login_url = '/student_login')
def profile(request):
    return render(request, "profile.html")

@login_required(login_url = '/student_login')
def edit_profile(request):
    student = Student.objects.get(user=request.user)
    if request.method == "POST":
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']

        student.user.email = email
        student.phone = phone
        student.branch = branch
        student.classroom = classroom
        student.roll_no = roll_no
        student.user.save()
        student.save()
        alert = True
        return render(request, "edit_profile.html", {'alert':alert})
    return render(request, "edit_profile.html")

def delete_book(request, myid):
    books = Book.objects.filter(id=myid)
    books.delete()
    return redirect("/view_books")

def delete_student(request, myid):
    students = Student.objects.filter(id=myid)
    students.delete()
    return redirect("/view_students")

def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert':alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong':currpasswrong})
        except:
            pass
    return render(request, "change_password.html")



def student_registration(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']
        image = request.FILES['image']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            passnotmatch = True
            return render(request, "student_registration.html", {'passnotmatch': passnotmatch})

        # Create user and student
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        student = Student.objects.create(user=user, phone=phone, branch=branch, classroom=classroom, roll_no=roll_no, image=image)
        
        # Save user and student
        user.save()
        student.save()

        # Send email confirmation
        subject = 'Account Created Successfully'
        message = f'Dear {first_name} {last_name},\n\nYour account has been created successfully! You can now log in using your credentials.\n\nThank you!'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        send_mail(subject, message, email_from, recipient_list)

        alert = True
        return render(request, "student_registration.html", {'alert': alert})
    return render(request, "student_registration.html")


def student_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return HttpResponse("You are not a student!!")
            else:
                return redirect("/profile")
        else:
            alert = True
            return render(request, "student_login.html", {'alert':alert})
    return render(request, "student_login.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return redirect("/add_book")
            else:
                return HttpResponse("You are not an admin.")
        else:
            alert = True
            return render(request, "admin_login.html", {'alert':alert})
    return render(request, "admin_login.html")

def Logout(request):
    logout(request)
    return redirect ("/")





















@login_required(login_url='/student_login')
def view_all_books(request):
    books = Book.objects.all()
    student = request.user.student
    requests = BookRequest.objects.filter(student=student)

    if request.method == "POST":
        book_id = request.POST.get('book_id')
        book = get_object_or_404(Book, id=book_id)

        existing_request = BookRequest.objects.filter(student=student, book=book).first()
        
        if not existing_request:
            new_request = BookRequest(status='pending', student=student, book=book)
            new_request.save()
            messages.success(request, "Your request has been submitted and is now pending approval.")
            print(f"Request submitted for Book ID: {book_id} by Student ID: {student.id}")                       # Redirect to the payment page with the new request ID
            return redirect(reverse('payment_view', args=[new_request.id]))
        else:
            # messages.warning(request, "You have already requested this book.")
            # print(f"Request already exists for Book ID: {book_id} by Student ID: {student.id}")
            new_request = BookRequest(status='pending', student=student, book=book)
            new_request.save()
            print(f"Request submitted for Book ID: {book_id} by Student ID: {student.id}")                       # Redirect to the payment page with the new request ID
            return redirect(reverse('payment_view', args=[new_request.id]))


    # Create a dictionary with book IDs as keys and request status as values
    request_status = {req.book.id: req.get_status_display() for req in requests}
    print(f"Request Status Dictionary: {request_status}")  # Print request statuses

    return render(request, "view_books_student.html", {
        'books': books,
        'request_status': request_status,
    })




# @login_required(login_url='/admin_login')
# def manage_requests(request):
#     requests = BookRequest.objects.all()
#     print(requests)  # Debugging line
#     return render(request, 'manage_requests.html', {'requests': requests})




@login_required(login_url='/admin_login')
def manage_requests(request):
    requests = BookRequest.objects.all()
    print(requests)  # Debugging line
    return render(request, 'manage_requests.html', {'requests': requests})




@login_required(login_url='/admin_login')
def approve_request(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.approved = True
    book_request.save()
    messages.success(request, "Request approved successfully!")
    return redirect('manage_requests')

@login_required(login_url='/admin_login')
def deny_request(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.delete()
    messages.success(request, "Request denied successfully!")
    return redirect('manage_requests')



@login_required(login_url='/student_login')
def request_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # # Check if the user has already requested the book
    # existing_request = BookRequest.objects.filter(student=request.user.student, book=book).first()
    # if existing_request:
    #     messages.warning(request, "You have already requested this book.")
    #     return redirect('view_all_books')

    if request.method == "POST":
        # Create the book request with status 'pending'
        BookRequest.objects.create(
            student=request.user.student,
            book=book,
            status='pending'  # Set initial status to pending
        )
        messages.success(request, "Book request submitted successfully!")
        return redirect('view_all_books')

    return render(request, "request_book.html", {'book': book})






@login_required(login_url='/admin_login')
def update_request_status(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)

    if request.method == "POST":
        new_status = request.POST.get('status')
        book_request.status = new_status
        book_request.save()
        messages.success(request, "Request status updated successfully!")
        return redirect('manage_requests')

    return render(request, "update_request.html", {'request': book_request})


@login_required(login_url='/student_login')
def book_details(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    print(book)
    return render(request, 'book_details.html', {'book': book})



# views.py
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactMessageForm

def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            # Send email to the admin
            send_mail(
                subject=contact_message.subject,
                message=contact_message.message,
                from_email=contact_message.email,
                recipient_list=['muhammadaltamash537@gmail.com'],  # Replace with the admin's email
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactMessageForm()
    return render(request, 'contact.html', {'form': form})


@login_required(login_url='/admin_login')
def view_contact_messages(request):
    messages = ContactMessage.objects.all().order_by('-created_at')  # Fetch all messages ordered by creation date
    return render(request, 'view_contact_messages.html', {'messages': messages})

@login_required(login_url='/admin_login')
def contact_message_detail(request, message_id):
    message = get_object_or_404(ContactMessage, id=message_id)
    return render(request, 'contact_message_detail.html', {'message': message})




# from library.forms import IssueBookForm
# from django.shortcuts import redirect, render, HttpResponse, get_object_or_404
# from .models import *
# from .forms import IssueBookForm
# from django.contrib.auth import authenticate, login, logout
# from . import forms, models
# from datetime import date
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages

# def index(request):
#     return render(request, "index.html")

# @login_required(login_url='/admin_login')
# def add_book(request):
#     if request.method == "POST":
#         name = request.POST['name']
#         author = request.POST['author']
#         isbn = request.POST['isbn']
#         category = request.POST['category']
        
#         # Handle file uploads
#         cover_image = request.FILES.get('cover_image')
#         pdf_file = request.FILES.get('pdf_file')

#         # Create the book instance
#         books = Book.objects.create(
#             name=name,
#             author=author,
#             isbn=isbn,
#             category=category,
#             cover_image=cover_image,
#             pdf_file=pdf_file
#         )
#         books.save()
        
#         messages.success(request, "Book added successfully!")
#         return redirect('add_book')  # Redirect to avoid resubmission
#     return render(request, "add_book.html")

# @login_required(login_url='/admin_login')
# def view_books(request):
#     books = Book.objects.all()
#     return render(request, "view_books.html", {'books': books})

# @login_required(login_url='/admin_login')
# def view_students(request):
#     students = Student.objects.all()
#     return render(request, "view_students.html", {'students': students})

# @login_required(login_url='/admin_login')
# def issue_book(request):
#     form = forms.IssueBookForm()
#     if request.method == "POST":
#         form = forms.IssueBookForm(request.POST)
#         if form.is_valid():
#             student_id = request.POST['name2']
#             isbn = request.POST['isbn2']

#             # Check if the book is already issued to the student
#             existing_issue = models.IssuedBook.objects.filter(student_id=student_id, isbn=isbn).exists()
#             if existing_issue:
#                 messages.warning(request, "This book has already been issued to the student.")
#                 return render(request, "issue_book.html", {'form': form})

#             # Create and save the new issued book record
#             obj = models.IssuedBook()
#             obj.student_id = student_id
#             obj.isbn = isbn
#             obj.save()
#             messages.success(request, "Book issued successfully!")
#             return render(request, "issue_book.html", {'obj': obj})
#     return render(request, "issue_book.html", {'form': form})

# @login_required(login_url='/admin_login')
# def view_issued_book(request):
#     issued_books = IssuedBook.objects.all()
#     details = []

#     for issued in issued_books:
#         days = (date.today() - issued.issued_date).days
#         fine = max(0, (days - 14) * 5)  # Fine calculation
        
#         # Fetch the book and student associated with the issued book
#         book = models.Book.objects.filter(isbn=issued.isbn).first()
#         student = models.Student.objects.filter(user=issued.student_id).first()
        
#         # Check if both book and student exist to avoid NoneType issues
#         if book and student:
#             detail = (student.user, student.user_id, book.name, book.isbn, issued.issued_date, issued.expiry_date, fine, book.id)
#             details.append(detail)

#     return render(request, "view_issued_book.html", {'issuedBooks': issued_books, 'details': details})

# @login_required(login_url='/admin_login')
# def delete_issued_book(request, book_id):
#     issued_book = get_object_or_404(IssuedBook, id=book_id)

#     if request.method == 'POST':
#         issued_book.delete()
#         messages.success(request, "Issued book deleted successfully!")
#         return redirect('view_issued_book')

#     return render(request, 'confirm_delete.html', {'issued_book': issued_book})

# @login_required(login_url='/student_login')
# def student_issued_books(request):
#     student = Student.objects.filter(user_id=request.user.id).first()
#     issuedBooks = IssuedBook.objects.filter(student_id=student.user_id)
#     li1 = []
#     li2 = []

#     for i in issuedBooks:
#         books = Book.objects.filter(isbn=i.isbn)
#         for book in books:
#             t = (request.user.id, request.user.get_full_name(), book.name, book.author, book.id)
#             li1.append(t)

#         days = (date.today() - i.issued_date)
#         d = days.days
#         fine = 0
#         if d > 15:
#             day = d - 14
#             fine = day * 5
#         t = (i.issued_date, i.expiry_date, fine)
#         li2.append(t)

#     return render(request, 'student_issued_books.html', {'li1': li1, 'li2': li2})

# @login_required(login_url='/student_login')
# def profile(request):
#     return render(request, "profile.html")

# @login_required(login_url='/student_login')
# def edit_profile(request):
#     student = Student.objects.get(user=request.user)
#     if request.method == "POST":
#         email = request.POST['email']
#         phone = request.POST['phone']
#         branch = request.POST['branch']
#         classroom = request.POST['classroom']
#         roll_no = request.POST['roll_no']

#         student.user.email = email
#         student.phone = phone
#         student.branch = branch
#         student.classroom = classroom
#         student.roll_no = roll_no
#         student.user.save()
#         student.save()
#         messages.success(request, "Profile updated successfully!")
#         return redirect('edit_profile')
#     return render(request, "edit_profile.html")

# def delete_book(request, myid):
#     books = Book.objects.filter(id=myid)
#     books.delete()
#     messages.success(request, "Book deleted successfully!")
#     return redirect("/view_books")

# def delete_student(request, myid):
#     students = Student.objects.filter(id=myid)
#     students.delete()
#     messages.success(request, "Student deleted successfully!")
#     return redirect("/view_students")

# def change_password(request):
#     if request.method == "POST":
#         current_password = request.POST['current_password']
#         new_password = request.POST['new_password']
#         try:
#             u = User.objects.get(id=request.user.id)
#             if u.check_password(current_password):
#                 u.set_password(new_password)
#                 u.save()
#                 messages.success(request, "Password changed successfully!")
#                 return redirect("change_password")
#             else:
#                 messages.error(request, "Current password is incorrect.")
#         except User.DoesNotExist:
#             messages.error(request, "User not found.")
#     return render(request, "change_password.html")

# def student_registration(request):
#     if request.method == "POST":
#         username = request.POST['username']
#         first_name = request.POST['first_name']
#         last_name = request.POST['last_name']
#         email = request.POST['email']
#         phone = request.POST['phone']
#         branch = request.POST['branch']
#         classroom = request.POST['classroom']
#         roll_no = request.POST['roll_no']
#         image = request.FILES['image']
#         password = request.POST['password']
#         confirm_password = request.POST['confirm_password']

#         if password != confirm_password:
#             messages.error(request, "Passwords do not match.")
#             return render(request, "student_registration.html")

#         user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
#         student = Student.objects.create(user=user, phone=phone, branch=branch, classroom=classroom, roll_no=roll_no, image=image)
#         user.save()
#         student.save()
#         messages.success(request, "Registration successful! You can now log in.")
#         return redirect("student_registration")
#     return render(request, "student_registration.html")

# def student_login(request):
#     if request.method == "POST":
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(username=username, password=password)

#         if user is not None:
#             login(request, user)
#             if request.user.is_superuser:
#                 messages.error(request, "You are not a student!")
#                 return redirect('student_login')
#             else:
#                 return redirect("/profile")
#         else:
#             messages.error(request, "Invalid username or password.")
#     return render(request, "student_login.html")

# def admin_login(request):
#     if request.method == "POST":
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(username=username, password=password)

#         if user is not None:
#             login(request, user)
#             if request.user.is_superuser:
#                 return redirect("/add_book")
#             else:
#                 messages.error(request, "You are not an admin.")
#         else:
#             messages.error(request, "Invalid username or password.")
#     return render(request, "admin_login.html")

# def Logout(request):
#     logout(request)
#     messages.success(request, "Logged out successfully.")
#     return redirect("/")

# @login_required(login_url='/student_login')
# def view_all_books(request):
#     books = Book.objects.all()
#     student = request.user.student
#     requests = BookRequest.objects.filter(student=student)

#     if request.method == "POST":
#         book_id = request.POST.get('book_id')
#         book = get_object_or_404(Book, id=book_id)

#         existing_request = BookRequest.objects.filter(student=student, book=book).first()
        
#         if not existing_request:
#             new_request = BookRequest(status='pending', student=student, book=book)
#             new_request.save()
#             messages.success(request, "Your request has been submitted and is now pending approval.")
#         else:
#             messages.warning(request, "You have already requested this book.")

#         return redirect('view_all_books')

#     request_status = {req.book.id: req.get_status_display() for req in requests}
#     return render(request, 'view_all_books.html', {'books': books, 'request_status': request_status})
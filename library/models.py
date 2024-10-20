from django.db import models
from django.contrib.auth.models import User
from datetime import datetime,timedelta


from django.db import models

class Book(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=50) # Ensure ISBN is unique
    category = models.CharField(max_length=50)
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)  # Allow null and blank
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)  # Allow null and blank
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Add price field

    def __str__(self):
        return f"{self.name} [{self.isbn}] - ${self.price}"



class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    classroom = models.CharField(max_length=10)
    branch = models.CharField(max_length=10)
    roll_no = models.CharField(max_length=3, blank=True)
    phone = models.CharField(max_length=10, blank=True)
    image = models.ImageField(upload_to="", blank=True)

    def __str__(self):
        return str(self.user) + " ["+str(self.branch)+']' + " ["+str(self.classroom)+']' + " ["+str(self.roll_no)+']'


def expiry():
    return datetime.today() + timedelta(days=14)
class IssuedBook(models.Model):
    student_id = models.CharField(max_length=100, blank=True) 
    isbn = models.CharField(max_length=13)
    issued_date = models.DateField(auto_now=True)
    expiry_date = models.DateField(default=expiry)
    def __str__(self):
        return f"stude id--{self.student_id}"
    



class BookRequest(models.Model):
    STATUS_CHOICES = [
        ('request', 'Request'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='request')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.book} - {self.status}"

    @classmethod
    def get_status_display_choices(cls):
        return cls.STATUS_CHOICES
    





class ContactMessage(models.Model):
    name = models.CharField(max_length=100 , null=True)
    email = models.EmailField(null=True)
    subject = models.CharField(max_length=200 , null=True)  # Added subject field
    message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"



# models.py

class Payment(models.Model):
    # book_request = models.OneToOneField(BookRequest, on_delete=models.CASCADE)
    book_request = models.ForeignKey(BookRequest, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)  # Consider encrypting sensitive data
    expiry_date = models.DateField()  # Use DateField for expiration date
    cvv = models.CharField(max_length=3)  # Keep CVV as a CharField, but ensure it's always 3 digits
    book_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Store book price
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        student = self.book_request.student
        return f"Payment for '{self.book_request.book.name}' by {student.user.get_full_name()} (Roll No: {student.roll_no})"

    @classmethod
    def create_payment(cls, book_request, card_number, expiry_date, cvv):
        return cls.objects.create(
            book_request=book_request,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            book_price=book_request.book.price  # Set book price during payment creation
        )

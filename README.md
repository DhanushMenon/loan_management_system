Loan Management System (Django REST API) 

Overview 

The Loan Management System API is a Django-based REST API designed to manage loans with user-defined monthly compound interest. The system provides:

•	Role-based authentication (Admin & User) using JWT
•	Loan creation, viewing, and foreclosure
•	Automatic interest calculation and repayment schedules
•	Secure OTP-based user registration
•	Swagger API documentation for easy API exploration

The backend is built using Django & Django REST Framework (DRF) with PostgreSQL as the database. Authentication is handled using JWT (Simple JWT), and OTP emails are sent via SMTP.


Live API URL 
Render Deployment:  https://loan-management-system-h1i5.onrender.com  


Tech Stack 

•	Backend: Django, Django REST Framework 
•	Database: PostgreSQL 
•	Authentication: JWT (Simple JWT) 
•	Email Service: SMTP 
•	Deployment: Render (Free Tier) 


Features & Requirements

1️. Authentication & Role-Based Access Control

•	JWT Authentication (Simple JWT)
•	Role-based access (Admin & User)
•	OTP email verification using Nodemailer
•	Secure API endpoints requiring valid tokens

2️. Loan Management Features

 Users can:

•	Add new loans (amount, tenure, interest rate)
•	View their loan history and active loans
•	Foreclose loans early (adjusted interest applies)

Admins can:

•	View all loans in the system
•	Access detailed loan information for any user
•	Delete loan records (Admins only)

3️. Loan Calculation

•	User-defined yearly compound interest
•	Automatic calculation of EMI, total payable, and interest
•	Loan repayment schedules generated upon loan approval
•	Foreclosure with adjusted interest calculations



Setup Instructions 

1. Clone the Repository 

•	git clone https://github.com/DhanushMenon/loan_management_system.git 
•	cd loan_management_system 

2️. Set Up a Virtual Environment 

•	python -m venv venv 
•	venv\Scripts\activate     

3️. Install Dependencies 

•	pip install -r requirements.txt 

4️. Set Up Environment Variables 

•	Create a .env file in the project root and add: 
DATABASE_URL=your_postgresql_url 
SECRET_KEY=your_secret_key 
DEBUG=False 
ALLOWED_HOSTS=localhost,12️7.0.0.1,loan-management-system-h1i5.onrender.com 

5. Run Migrations 

•	python manage.py migrate 

6️. Create Superuser (Admin) 

•	python manage.py createsuperuser 

7. Start the Development Server 

• python manage.py runserver 


API Endpoints 

Method 	 Endpoint 	          	Description 
POST 	/api/auth/register/ 	  	Register a new user 
POST 	/api/auth/login/ 	  	Login and get JWT token 
POST 	/api/auth/resend-otp/ 	  	Resend OTP for email verification
GET 	/api/loans/ 	          	List all loans (User/Admin) 
POST 	/api/loans/ 	          	Create a new loan 
GET 	/api/loans/{id}/ 	  	Get loan details 
POST 	/api/loans/{id}/foreclose/ 	Foreclose a loan 
POST 	/api/loans/{id}/make_payment/ 	Make a loan payment 
DELETE 	/api/loans/{id}/ 		Delete a loan (Admin only) 

 
API Documentation 

•	The API is documented using Swagger(Instead of Postman/Thunder Client). 
•	Can view it online or use the Swagger JSON file.
•	Live API Docs: [API Swagger UI] ( https://loan-management-system-h1i5.onrender.com/swagger/ ) 
•	Swagger JSON: [`docs/loan_management_api_swagger.json`] (docs/loan_management_api_swagger.json)




 

# 📚 **Library Management System API**  

A **Flask-based Library Management System API** that allows users to **borrow, return, and manage books** with secure authentication and authorization.  

### **🔑 Features:**  
- **User Authentication & Authorization** (JWT-based)  
- **Role-based Access Control** (Admin, Librarian, Member)  
- **Book Borrowing & Returning System**  
- **Email Notifications** (Borrowing confirmation & reminders)  
- **Two-Factor Authentication (2FA)** via email  
- **Forgot Password & Reset System**  

### **⚡ Technologies Used:**  
- Flask & Flask-RESTful  
- Flask-JWT-Extended (Authentication)  
- Flask-SQLAlchemy (Database ORM)  
- Flask-Mail (Email notifications)  
- MySQL (Database)  

### **🚀 Getting Started**  
1. **Clone the repository:**  
   ```bash
   git clone https://github.com/your-username/library-management-api.git
   cd library-management-api
   ```
2. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables** (e.g., database URL, email credentials).  
4. **Run the application:**  
   ```bash
   flask run
   ```
5. **API is available at:** `http://127.0.0.1:5000/api/`  

### **📌 Endpoints Overview:**  
| Method | Endpoint | Description |
|--------|---------|------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | User login with JWT |
| POST | `/api/auth/verify-2fa` | Two-factor authentication |
| POST | `/api/borrow/` | Borrow a book |
| PUT | `/api/borrow/return/<borrow_id>` | Return a borrowed book |
| GET | `/api/books` | Fetch available books |

---

📌 **Contributions & Issues:**  
Feel free to **open an issue** or **submit a pull request** if you'd like to contribute! 🚀  

💡 **Developed with ❤️ using Flask**

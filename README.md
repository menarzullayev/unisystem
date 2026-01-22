# Unisystem - AI-Powered Education Platform

Unisystem is a Django-based intelligent education management system with AI-powered features for essay grading, exam proctoring, and educational content analysis.

## 🚀 Features

- **AI Essay Grading**: Automatic essay evaluation and feedback using Google Gemini API
- **Intelligent Exam System**: AI-powered exam session management and proctoring
- **Education Agents**: Specialized AI agents for different educational tasks
- **HEMIS Integration**: Integration with education management system
- **Chat Interface**: Real-time chat with AI assistants
- **Multi-user Support**: Teacher and student roles with different permissions
- **Media Management**: Support for essay submissions and educational materials

## 🛠️ Technology Stack

- **Backend**: Django 5.0+
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **API**: Google Gemini API for AI capabilities
- **Frontend**: HTML/CSS/JavaScript with Django templates
- **Python**: 3.12+

## 📋 Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/menarzullayev/unisystem.git
   cd unisystem
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your:
   - Google Gemini API keys
   - Django secret key
   - Other configuration settings

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Start the development server**
   ```bash
   python manage.py runserver
   ```

   Access the application at `http://localhost:8000`

## 📁 Project Structure

```
unisystem/
├── chat/                 # Chat application with AI agents
├── core/                 # Core functionality and models
├── edu/                  # Education module
├── config/               # Django configuration
├── templates/            # HTML templates
├── media/                # User-uploaded files
├── manage.py             # Django management script
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🤖 AI Agents

### Available Agents

- **Universal Agent**: General-purpose AI assistant
- **Education Agent**: Educational content and learning support
- **Essay Agent**: Essay evaluation and feedback
- **HEMIS Agent**: Education system integration
- **Exam Agent**: Exam management and proctoring

## 🔐 Security

- Never commit `.env` file to version control
- Use `.env.example` as a template for required variables
- Keep API keys secure and rotate regularly
- Enable DEBUG=False in production

## 📝 Configuration

### Environment Variables

- `GEMINI_KEY_STUDENT`: API key for student features
- `GEMINI_KEY_EDUCATION`: API key for education module
- `GEMINI_KEY_ESSAY`: API key for essay grading
- `GEMINI_KEY_EXAM`: API key for exam features
- `GEMINI_KEY_GENERAL`: API key for general features
- `DEBUG`: Django debug mode (True/False)
- `SECRET_KEY`: Django secret key for security
- `ALLOWED_HOSTS`: Allowed host domains

## 🚀 Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production database (PostgreSQL recommended)
3. Configure `ALLOWED_HOSTS` with your domain
4. Use a production WSGI server (Gunicorn, uWSGI)
5. Set up HTTPS with SSL certificates
6. Configure proper email backend
7. Use environment-specific settings

## 📚 Usage

### Admin Panel
Access Django admin at `/admin` with superuser credentials.

### Student Portal
- View available exams and assignments
- Submit essays for AI evaluation
- Track grades and progress

### Teacher Dashboard
- Create and manage exams
- Review essay submissions
- Grade essays and provide feedback
- View student analytics

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📧 Support

For support and questions:
- Open an issue on GitHub
- Contact the development team

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Django community for the excellent framework
- All contributors and users

---

**Last Updated**: January 22, 2026

Made with ❤️ by the Unisystem Team

# SummaryFinance

AI-powered news analysis and summarization platform.

## Technologies

### Backend

- Spring Boot
- MySQL
- JPA/Hibernate
- Swagger UI

### AI Service

- Python FastAPI
- Google Gemini AI
- OpenAPI

### Frontend (Coming Soon)

- Next.js
- TypeScript
- Tailwind CSS

## Setup

### Prerequisites

- Java 17+
- Python 3.9+
- MySQL 8.0+
- Node.js 18+ (for future frontend)

### Installation

1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SummaryFinance.git
cd SummaryFinance
```

2. Backend Setup

```bash
cd backend
# Copy example properties and update with your credentials
cp src/main/resources/application.properties.example src/main/resources/application.properties
# Run the application
./mvnw spring-boot:run
```

3. AI Service Setup

```bash
cd ai-service
# Copy example env and update with your API key
cp .env.example .env
# Setup Python environment and dependencies
./setup.bat
# Run the service
./run.bat
```

## API Documentation

- Backend API: http://localhost:8080/swagger-ui.html
- AI Service API: http://localhost:8000/docs

## Environment Configuration

### Backend

Update `application.properties` with your MySQL credentials:

```properties
spring.datasource.username=your_username
spring.datasource.password=your_password
```

### AI Service

Update `.env` with your Google Gemini API key:

```env
GOOGLE_API_KEY=your_api_key_here
```

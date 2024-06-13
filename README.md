# Telegram Bot for Educators and Students

## Overview

This project is a Telegram bot designed to facilitate interaction between teachers and students, both individually and in group (team) formats. It allows teachers to create assignments, receive submissions, grade students, and generate convenient reports in Excel format. Curators are assigned by the administrator, defined by the `ADMIN_TELEGRAM_ID` variable in the `.env` file.

## Author

**Saidov David**  
Email: [delightxxls@gmail.com](mailto:delightxxls@gmail.com)

## Technologies Used

- **Python-Telegram-Bot 21.1.1**: A library to interact with the Telegram Bot API.
- **SQLAlchemy 2.0.30**: SQL toolkit and Object-Relational Mapping (ORM) library.
- **AioSQLite 0.20.0**: Asynchronous SQLite database support for Python.
- **Python-Dotenv 1.0.1**: Read key-value pairs from a `.env` file and set them as environment variables.
- **Nest-Asyncio 1.6.0**: Allows running asyncio event loops in a nested context.
- **Pandas 2.2.2**: Conveniently generate Excel-files.
- **APScheduler 3.10.4**: A library to schedule Python jobs.

## Functionality

- **Task Scheduling**: APScheduler is used to schedule the sending of individual and group tasks at specified times, ensuring that notifications are sent out promptly.
- **Notifications**: Python-Telegram-Bot is used to send notifications to students and teachers about new tasks, deadlines, and other important updates.
- **Database Management**: SQLAlchemy and AioSQLite are used to manage and query the database, ensuring efficient storage and retrieval of user and task information.
- **Data Analysis and Reporting**: Pandas is useto generate and export these reports in Excel format.
- **Configuration Management**: Python-Dotenv is used to manage environment variables securely, including API keys and database connection details.
- **Async Operations**: Nest-Asyncio is used to allow nested asynchronous operations, ensuring smooth execution of concurrent tasks without blocking the bot's main functionalities.
- **Logging**: The bot uses Python's logging module to create detailed logs of its operations. Logs are stored in the `logs` directory with a file named `bot.log`. The log files are rotated at midnight, and up to three backup files are kept. A custom filter is used to exclude specific log records, ensuring clean and relevant log output.

## Getting Started

### Environment Variables

To start the bot, you need to set up the environment variables from the `.env_example` file. Make sure to configure the following:

- `ADMIN_TELEGRAM_ID`: The Telegram ID of the TG user, who is going to function as an Administrator.
- `TIMEZONE_OFFSET`: Set the timezone offset (e.g., `3` for UTC+3 or `-3` for UTC-3).
- `BOT_TOKEN`: Set the token you've got from the BotFather in order to run the code in your bot instance.
- `DATABASE_PATH`: If you don't have any specific preferences for the database, you may pass to an `.env` file the value from `.env_example`.

### Running the Bot

You can run the bot by either executing the `main.py` file or using `docker-compose.yml`.

#### Running with Python

1. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Run the bot:
    ```sh
    python main.py
    ```

#### Running with Docker

1. Build and run the container using Docker Compose:
    ```sh
    docker-compose up --build -d
    ```

## GitHub Actions Workflow (CI/CD)

This project includes a GitHub Actions workflow for continuous deployment. The workflow:

1. Builds the Docker image and pushes it to DockerHub on each push to the `main` branch.
2. Deploys the updated Docker image to a remote server.

By following these instructions and utilizing the provided technologies, you can effectively deploy and manage the Telegram bot for educators and students.

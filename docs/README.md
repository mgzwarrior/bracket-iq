# bracket-iq
A tool for creating, scoring, comparing, and analyzing NCAA March Madness brackets.  Including an AI model for predicting winners in the tournament.

## Development

### Prerequisites
- Docker - be sure to have Docker installed on your machine.  You can download it [here](https://www.docker.com/products/docker-desktop)
- Python 3.8 - be sure to have Python 3.8 installed on your machine.  You can download it [here](https://www.python.org/downloads/)
- Django Migrations - be sure to run all Django migrations for the `backend` app by running the following commands from the root directory of the project:
```
cd backend
python manage.py makemigrations backend
python manage.py migrate
```

### Running the Django App
Start the Django app as a docker container by running the following command in the `/backend` directory of the project:
```
docker-compose up
```
The app will be available at http://localhost:8000
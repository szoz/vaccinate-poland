# vaccinate-poland

Web application supporting COVID-19 vaccination in Poland. 

Application is deployed on Heroku. API documentation is available at: 

http://vaccinate-poland.herokuapp.com/docs
http://vaccinate-poland.herokuapp.com/redoc
	
## Technologies
Project is created with:
* [FastAPI](https://fastapi.tiangolo.com/)
* Python 3.8
* [Pipenv](https://github.com/pypa/pipenv)

[Pytest](https://docs.pytest.org/en/6.2.x/) was used for testing.
	
## Setup
To run this project install dependencies using Pipenv for production environment:
```
$ pipenv install --ignore-pipfile
```

or development environment:
```
$ pipenv install --dev
```

Finally, run application with Uvicorn:
```
$ uvicorn main:app
```

# Album Project

My name is Mateusz. I am a self-taught programmer who started learning out of curiosity. 
I would like to work with experienced engineers to learn best practices and develop my skills.


The project serves as a digital album to store our photos. A user can have only 3 albums and 10 photos in each.
As this is a portfolio project, the size of the images is limited to 1MB.


To make full use of the application, you need to [create an account](https://) and [obtain an access token](https://).


The [Documentation](https://) allows you to test the endpoints, but you can also do this using a browser.


To try it in the [browser](https://), you will need the google Modheader extension to add the token to your headers.

example: header name: `Authorization`, value: Bearer `your code`

## Run Locally

Clone the project

```bash
  git clone https://github.com/mateuszklusowski/django-rest-api
```

Go to the project directory

```bash
  cd django-rest-api
```

Install dependencies

```bash
  docker-compose build
```

Start the server

```bash
  docker-compose up
```

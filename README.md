# Album Project
A digital album REST API is a project that involves creating a server-side application programming interface (API) that enables clients to interact with a digital album stored on a server. 

The API allows clients to retrieve information about the album, such as its title and images list, as well as perform actions on the album, such as adding or removing images. 

The API follows the REST architectural style. 

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

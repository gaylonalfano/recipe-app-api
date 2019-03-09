# -- Image you are going to inherit
FROM python:3.7-alpine
# (optional) Who's maintaining the project
LABEL maintainer="Gaylon Alfano"

# Set the Python unbuffered environment variable
# Recommended when running Python within Docker containers
# It doesn't allow Python to buffer the outputs. Just prints directly.
# This avoids complications with Docker image when running your Python app.
ENV PYTHONUNBUFFERED 1

# -- Store our dependencies in a requirements.txt file and copy to docker image
COPY ./requirements.txt /requirements.txt

# Encountered a WARNING after building. Need to add this line before postgresql
RUN apk update

# Add dependencies so we can install the psycopg2 package for Django/Postgres
# Add jped-dev binaries to our permanent dependencies:
RUN apk add --update --no-cache postgresql-client jpeg-dev

# Add temp packages needed to install requirements. Assigning alias
# See notes. Adding temp dependencies for installing Pillow package
RUN apk add --update --no-cache --virtual .tmp-build-deps \
  gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev

# -- Installs our requirements into the Docker image
RUN pip install -r /requirements.txt

# Delete the temporary dependencies we just added
RUN apk del .tmp-build-deps

# -- Make a directory inside our image to store our application's source code
RUN mkdir /app

# -- Switch to this new directory (like cd basically) and set as default
# Any application we run from the Docker container will run from this directory
WORKDIR /app

# -- Copies from local machine /app folder to the /app folder on our image.
# This allows us to copy our code we create and copy to our Docker image.
COPY ./app/ /app

# Create static and media folders for storing static files so we don't
# get permission errors. Current using root user to execute these steps.
RUN mkdir -p /vol/web/static
RUN mkdir -p /vol/web/media

# -- Create a user that is going to run our application using Docker
# The "-D" specifies that the user will ONLY run our process from our project.
RUN adduser -D user

# -- Change ownership of static and media directories to user
RUN chown -R user:user /vol/

# -- Add permissions to allow owner/user to do anything, others read/execute
RUN chmod -R 755 /vol/web

# -- Switches Docker to the user we just created. This is for security. Limits their scope.
# If we don't use this then the image will run using the root account.
# That means if somebody compromises our application they can have root access
# to the whole image.
USER user
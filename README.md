<div align="center">
  <img src="./assets/logo.png" width="450" />
  
  # pressReadMePlease
  
  A process for automating PressReader weekly token automagically.
  <br/><br/>
  
  [![MIT](https://img.shields.io/github/license/tatoalo/pressReadMePlease)](https://github.com/tatoalo/pressReadMePlease)
  [![Pulls from DockerHub](https://img.shields.io/docker/pulls/tatoalo/pressreader-automation.svg)](https://hub.docker.com/r/tatoalo/pressreader-automation)
</div>

Using MLOL and PressReader to read newspapers from all over the world is pretty handy, if you use the mobile apps only, though, it may become pretty painful to remember once every week to manually login into MLOL and then PressReader from the dekstop version so that PressReader doens't throw you out of their system.

With pressReadMePlease you can automate this, **set it and forget it!**.

By default the authentication token updating procedure will launch every Friday at 2.30am, of course you can edit this scheduling in the related crontab file.

## Quick Start w/ Docker

You can [pull](https://hub.docker.com/r/tatoalo/pressreader-automation) the Docker image, subsequently launch the container with:

```
docker run --name pressreader -itd --restart unless-stopped tatoalo/pressreader-automation
```

### Authentication Data

The application, in order to properly function, requires a file `auth_data.txt` located in the `/src/` directory, where the source code lives.

You can add this file in various ways:
1. Mount it as volume when running the container
2. Clone the repo, edit the `Dockerfile` by adding ``` COPY src/auth_data.txt src/ ```, then ``` $ docker build -t pressreader-automation . ``` and run as previously mentioned
3. **Easy-peasy method**, pull the image, run it as shown above and then access the running container with ```$ docker attach pressreader```, here navigate to `src/` and `vi auth_data.txt` where you can easily paste your credentials. Remember to exit the session with `CTRL` + `P` and then `CTRL` + `Q`

The format required is:
```
    direct link of MLOL webpage (it depends to which library you're affiliated with)
    email address MLOL account
    password MLOL account
    email address PRESSREADER account
    password PRESSREADER account
```
one information per line, on the first run of `main.py` you'll receive a message back telling you to populate the file if it wasn't there to begin with.
e.g.:
```
$ cat auth_data.txt
  https://milano.medialibrary.it/home/index.aspx
  test@test.com
  testing!
  test2@test.com
  testing2!
```

### Watchtower support
If you want, you can run this beside [Watchtower](https://github.com/containrrr/watchtower) which allows you to automatically keep all your images up-to-date.

## Clone the repo

You can clone the repo and launch it as is (requires *Chrome/Chromium, chromedriver + selenium*). 


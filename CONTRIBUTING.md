# Contribution Guide

Make sure that you've setup the repository locally as described in the [README](README.md) file first,
then follow the steps below to start contributing.

Contribution in this repository requires:

- Python 3.8 or higher (tested on max 3.10.x)
- pip >= 20.0.0 (tested on max 22.x)
- MongoDB 5.0.x connection string (mongodb://user:password@host:port/database)
- Redis 6.x or higher connection string (redis://user:password@host:port)
- Both main/.env and main/.env.testing files created & setup properly
- A python virtual environment (`python3 -m venv virtual-environment-name` or `mkvirtualenv virtual-environment-name`)
- A bot user setup in database using `createsuperuser` with email address same as `BOTMAIL` in your main/.env
- A queue cluster running separately using `qcluster` command
- The server running on `http://127.0.0.1:8000` using `runserver` command
- Ensure that you're able to view the localhost Knotters homepage from browser.
- Knowing that `127.0.0.1:8000` represents `localhost:PORT` and not some kind of weird telephone number.
- Knowledge of Python, Django Framework, MongoDB, Redis, Git, HTML, CSS, JavaScript, Web2.0, Linux, Programming, Typing, Breathing, etc.

Now assuming that you've ensured everything from above list successfully, you can start learning about the structure of this project, following.

## Structure

The source code structure of this project is of any typical Django based project (with some additional files and folders which will be discussed later, keep reading). However, to know the full extent of what this source code is meant to do, you need to understand the project from a user's perspective in a simpler way.

### From user's perspective

You visit [`https://knotters.org`](https://knotters.org]) (or in your case, [`http://127.0.0.1:8000`](http://127.0.0.1:8000)) using your modern browser. In case of visiting knotters.org, your browser attaches the default port 443 (on https) or 80 (on http) for equivalence with your 8000 of localhost. The final request is sent your ISP to check for the associated IP address with the name `knotters.org` in something called DNS records. Now since we (us at knotters.org) have provided our server's IP address for our domain name (we use Google Domains service for this, something like GoDaddy), your ISP gets it and proceeds towards the same through the internet, and finally reaches our server for you, carrying your request data (there are many things your browser attaches automatically with your request, like your own IP address). This is exactly what your ISP charges you for.

Now, our server, just like yours at `127.0.0.1:8000`, has this repository set up and running on `server-ip-address:443` (actually it is more complicated, involving - firewall, reverse-proxy, etc., but we're looking at things from user's perspective). Now at this point, the Django application running on server receives the request, and checks the part following the `:PORT`, which is in this scenario, is `/` (like in `https://knotters.org/`, `http://server-ip-address:443/`, `http://127.0.0.1:8000/`, the end `/` part).

As soon as Django recognizes the path, it finds the function linked with this path and executes it (which our developers have wrote and linked in source code). Now, whatever this function decides/wants to do, one thing that it surely needs to do is to return something, because

- You are waiting for your browser to show something
- Your browser is waiting for your ISP to provide something.
- Your ISP is waiting for our server to return something
- Our server is waiting for our Django application to say something
- Our Django application is waiting for the `/` path linked function to respond with something

Now, because we wanted to show some nice combination of texts, images and colors to you whenever you visit our server like this, we wrote our function to respond to such request with data containing information in HTML language, as we know that when this will reach your browser, it will understand the language and will decode it nicely into a page that we want you to see.

So, the linked function thankfully does its job (0.02s), and responds with what we instructed it to do (and with additional data, like your device's IP address which your browser provided us in request). The response is then received by your ISP (0.08s), which hopefully does not alter with it (in some cases it does!), then your ISP then returns it to your browser using the your IP address that we provided in response so that it reaches to you only (0.4s), and upon seeing that the response contains text in HTML format, your browser starts decoding it, and you see the nice homepage of Knotters, loading on your screen (0.5s).

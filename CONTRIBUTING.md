# Contribution Guide

Make sure that you've setup the repository locally as described in the [README](README.md) file first,
then follow the steps below to start contributing.

Contribution in this repository requires:

- Python 3.8 or higher (tested on max 3.10.x)
- pip >= 20.0.0 (tested on max 22.x)
- MongoDB 5.0.x connection string (mongodb://user:password@host:port/database)
- Redis 6.x or higher connection string (redis://user:password@host:port)
- Git version 2.35.x or above
- Both main/.env and main/.env.testing files created & setup properly
- A python virtual environment (activated) with all dependencies installed from our [requirements.txt](requirements.txt).
- A bot user setup in database using `createsuperuser` with email address same as `BOTMAIL` in your main/.env
- A queue cluster running separately using `qcluster` command
- The server running on `http://127.0.0.1:8000` using `runserver` command
- Ensure that you're able to view the localhost Knotters homepage from browser.
- Knowing that `127.0.0.1:8000` represents `localhost:PORT` and not some kind of weird telephone number.
- Knowledge of Python, Django Framework, MongoDB, Redis, Git, GitHub, HTML5, CSS3, JavaScript (ES6), Web2.0, Linux, Nginx, Gunicorn, Programming, Debugging, not running away from errors, Google Search, StackOverflow, **Reading**, Typing, Breathing, etc.

Now assuming that you've ensured everything (or at least something) from above list successfully, you can start learning about the working of this project.

## Working

Before working on the source code, you should know how the source code works. To know the full extent of it and what it is meant to do, you need to understand the working of project from a new developers's perspective in a simpler way.

### Simple perspective

You visit [`https://knotters.org`](https://knotters.org]) (or in your case, [`http://127.0.0.1:8000`](http://127.0.0.1:8000)) using your modern browser. In case of visiting knotters.org, your browser attaches the default port 443 (on https) or 80 (on http) for equivalence with your 8000 of localhost. The final request is sent your ISP to check for the associated IP address with the name `knotters.org` in something called DNS records. Now since we (us at knotters.org) have provided our server's IP address for our domain name (we use Google Domains service for this, something like GoDaddy), your ISP gets it and proceeds towards the same through the internet, and finally reaches our server for you, carrying your request data (there are many things your browser attaches automatically with your request, like your own IP address). This is exactly what your ISP charges you for.

Now, our server, just like yours at `127.0.0.1:8000`, has this repository set up and running on `server-ip-address:443` (actually it is more complicated, involving - firewall, reverse-proxy, etc., but we're looking at things from user's perspective). Now at this point, the Django application running on server receives the request, and checks the part following the `:PORT`, which is in this scenario, is `/` (like in `https://knotters.org/`, `http://server-ip-address:443/`, `http://127.0.0.1:8000/`, the end `/` part).

As soon as Django recognizes the path, it finds the function linked with this path and executes it (which our developers have wrote and linked in [`main/urls.py`](main/urls.py)). Now, whatever this function decides/wants to do, one thing that it surely needs to do is to return something, because

- You are waiting for your browser to show something
- Your browser is waiting for your ISP to provide something.
- Your ISP is waiting for our server to return something
- Our server is waiting for our Django application to say something
- Our Django application is waiting for the `/` path linked function to respond with something

Now, because we wanted to show some nice combination of texts, images and colors to you whenever you visit our server like this, we wrote our function to respond to such request with data containing information in HTML language, as we know that when this will reach your browser, it will understand the language and will decode it nicely into a page that we want you to see.

So, the linked function thankfully does its job, and responds with what we instructed it to do (and with additional data, like your device's IP address which your browser provided us in request). The response is then received by your ISP, which hopefully does not alter with it (in some cases it does!), then your ISP then returns it to your browser using the your IP address that we provided in response so that it reaches to you only, and upon seeing that the response contains text in HTML format, your browser starts decoding it, and you see the nice homepage of Knotters, loading on your screen.

Now, the study of received & decoded HTML in your browser is itself a separate domain, known as frontend. For our current request, the HTML response contains links to resources like images, styles and scripts (not the resources themselves, just links to them). So, you need to request each of the mentioned link in HTML code to get the resources for you, just like you requested the link to our homepage for html resource, and for every such link the same above mentioned request-response procedure will happen.

But, as an html code can contain numerous amount of links to such kind of resources, your browser does this heavy-lifting for you by finding such links in the received html and sending requests for each of them on behalf of you. Then, it decodes & displays the image responses (png/svg/jpg), executes the style responses (css), and runs the code in script responses (js) in the sequence which their links are mentioned in the html code (but not always).

For all kind of requests, including the requests to static resources (images/styles/scripts), each of them has a unique path, just like our hompage has a unique `/` path. For example, a full script path can look like `https://knotters.org/static/2.6.4/scripts/sw.js` or [`https://knotters.org/service-worker.js`](https://knotters.org/service-worker.js), and you can visit these kind of links directly from your browser's address bar. But this time, do not expect a nice colorful page, as the in response to these links our server will not return any HTML code for your browser to play with, but plain text based responses which will be displayed to you as they are. Similarly & accordingly for other resources like images, styles, fonts, manifests, texts, XMLs, PDFs, etc.

> Along with response content of any kind, a status code is also always sent in response, which helps the browser determine the state of response. For example, you already know about 404. 404 is one of the status codes defined in http protocol used uniformly by the whole world. If you request something using http (or https), and receive a response containing 404 status code, then it signifies that whatever you tried to look for, does not exists on server. Similarly there are many other status codes for different purposes of each, you can check all of them [from here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status). The beauty here is, you'll receive a response by visiting the provided link, containing its own http status code, while also containing information of all http status codes for you to know about.

So, a frontend developer has to play around with how and when such resources will be used in any kind of html response (remember that apart from homepage, there are other paths as well through which server returns different HTML responses), so that whenever users visit some popular paths like [`https://knotters.org/login`](https://knotters.org/login) or [`https://knotters.org/signup`](https://knotters.org/signup) using their browsers, they should be able to see well designed colorful pages with cool buttons to play around with, and should be willing to provide whatever we ask from them using the HTML hypnosis. This is what a frontend developer should aim to achieve while writing any part of HTML, CSS or Javascript code for knotters.org and its subdomains.

And as far as a backend developer is concerned, one of the most important things they have to focus on while writing code, is the speed of their logic, as you have seen that from the mentioned request-response procedure, you had to wait for so many checkpoints to receive a response for your request, and all of it depended on how fast the path attached function was able to return something, considering that your internet speed was high. So, a backend developer creates the path attached functions for different kinds of paths (`/`, `/login`, `/projects`, etc.) to execute some logic depending upon request data, and return relevant response accordingly as soon as possible. The user doesn't like to wait and wants to receive responses quickly, and if knotters.org is impressing them in that way, it is more likely that they will provide anything & move anywhere on our platform, whatever & wherever we ask them to provide & navigate, using the speedy response hypnosis.

Now that you know how Knotters is utilizing the http protocol of internet, you can proceed with structure of this project.

## Structure

The source code structure of this project is of any typical Django based project, with some additional files and folders which will be discussed, keep reading.

The platform itself contains the following global sections

- Projects
- Community
- Competitions
- Management

Each of the sections contain sub-sections for particular things. Therefore, a similar pattern is being followed in organization of source code too. You'll find the following folders in repository

- `main/` For the application wide code
- `auth2/` For authentication related code
- `people/` For community
- `projects/` For projects
- `compete/` For competitions
- `moderation/` For moderation
- `management/` For management

The following section will explain you the purpose of each directory, and other non-mentioned directories as well.

### Sections

#### `main/`

This folder contains project-wide configuration, resources, links, functions and the entry point of the application (from both developer and application's perspective).

#### `auth2/`

#### `people/`

#### `projects/`

#### `compete/`

#### `moderation/`

#### `management/`

There are, as a matter of fact, other folders as well, for different purposes, explained following

#### `static/`

Static code

#### `templates/`

All the dynamic response serving files for all sections of the platform are kept in this, most of them are supposed to be served as `html` in responses, while some of them as `js` as well. The directory structure inside this folder follows the same pattern of sections, where files are divided as

- `templates/projects/` templates related to projects section
- `templates/people/` templates related to community section
- `templates/compete/` templates related to competitions section
- `templates/management/` templates related to management section

There are, again, other sub-sections as well, which are either used by some pre-installed modules, or contain non-specific-to-any-section kind templates.

You can put any kind of file here which is supposed to be served dynamically as response, in appropriate section. By dynamically, we mean that all these files are used & manipulated by backend path functions to generate responses according to received request. For example, if you visit the URL [`https://knotters.org/@knottersbot`](https://knotters.org/@knottersbot), you are able to view specific details of a person, organized in html format (you already know why the html format). Similarly if you visit someone else's profile URL, you'll see the same structural organization of html content but with different specific details. This is happening because

- When you request `/@knottersbot` path, this kind of path is being checked against the relevant function, just like `/` path, and the function which is attached to it knows that a username has to be in the path.
- The function then extracts the username part, finds the specific user details from database (more on database later), picks up the particular html file from `templates/` folder which it is instructed to pick, loads the content of that file in memory, replaces the pre-assigned areas in the html content with user details, and returns the final prepared html data from memory as response.

Similarly, when you visit some other user's `/@username` path, same procedure happens, and because the html template file remains the same, the final html structure remains the same. The only thing that gets changed is the information being displayed in specific areas of the final html, which in this case, depends solely on the username contained in the requested path.

Most of the path functions in our platform work on similar principle. Using data from request which can be anything that your browser sent along (in this case it was the path itself), they prepare and return the dynamic response using template files from `templates/` folder.

> Some dynamic html responses also require javascript files for them to be preset with dynamic code, therefore you'll see a `scripts/` directory inside subdirectories of `templates/` directory for that purpose. Also a single path & function pair handles requests for all dynamic scripts requests, can be found in [`main/urls.py`](main/urls.py)

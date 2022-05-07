# Contribution Guide

Make sure that you've setup the repository locally as described in the [README](README.md) file first,
then follow read the explanation below to start contributing.

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
- Knowledge of Python, Django Framework, MongoDB, Redis, Git, GitHub, HTML5, CSS3, JavaScript (ES6), Service Worker (PWA), Web2.0, Linux, Nginx, Gunicorn, Programming, Debugging, not running away from errors, Googling, StackOverflowing, **Reading**, Typing, Breathing, etc.

Now assuming that you've ensured everything (or at least a few things) from above list successfully, you can start learning about the working of this project.

## Working

Before working on the source code, you should know how the source code works. To know the full extent of it and what it is meant to do, you need to understand the working of project from a new developers's perspective in a simpler way.

You visit [`https://knotters.org`](https://knotters.org) (or in your case, [`http://127.0.0.1:8000`](http://127.0.0.1:8000)) using your modern browser. In case of visiting knotters.org, your browser attaches the default port 443 (on https) or 80 (on http) for equivalence with your 8000 of localhost. The final request is sent your ISP to check for the associated IP address with the name `knotters.org` in something called DNS records. Now since we (us at knotters.org) have provided our server's IP address for our domain name (we use Google Domains service for this, something like GoDaddy), your ISP gets it and proceeds towards the same through the internet, and finally reaches our server for you, carrying your request data (there are many things your browser attaches automatically with your request, like your own IP address). This is exactly what your ISP charges you for.

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

Now that you know how Knotters is working on the http protocol of internet, you can proceed with structure of this project.

## Structure

The source code structure of this project is of any typical Django based project, with some additional files and folders which will be discussed, keep reading.

The platform itself contains the following global sections

- _Community_
- _Projects_
- _Competitions_
- _Management_
- _Moderation_

Each of the sections contain sub-sections for particular features for user. A similar pattern is being followed in organization of their relevant source code too. You'll find the following folders in repository

- [`main/`](main/) For application wide code
- [`auth2/`](auth2/) For authentication related code
- [`people/`](people/) For community
- [`projects/`](projects/) For projects
- [`compete/`](compete/) For competitions
- [`moderation/`](moderation/) For moderation
- [`management/`](management/) For management

The following section will explain you the purpose of each directory, and other non-mentioned directories as well.

### Sections

#### [`main/`](main/)

This folder contains project-wide configuration, resources, links, functions and serves as the entry point of the application (from both developer and application's perspective). Apart from the default Django required files, this directory also holds the following

- `.env` & `.env.testing` files containing your environment variables
- [env.py](main/env.py) to access the environment variables as python objects in other files
- [bots.py](main/bots.py) for functions & objects to access third party services like GitHub, Discord, Sender.net, etc.
- [exceptions.py](main/exceptions.py) for custom application wide exceptions
- [mailers.py](main/mailers.py) for functions related to emailing
- [middleware.py](middleware.py) contains application-wide middlewares for global requests/response data processing, each for their own purpose used in `MIDDLEWARE` list of [settings.py](main/settings.py). **The sequence of middlewares in that list is important**.
- [strings.py](main/strings.py) All the strings being used in whole application are stored and imported from here in form of objects, grouped by classes for different purposes. **All the urls and template names for every module are also and only exported from here via `class URL` and `class Template`**.

The [urls.py](main/urls.py) here handles the main requests and forwards the sub-section requests to other modules' urls.py handlers.
The [context_processors.py](main/context_processors.py) adds global context data to all template renderers, like `VERSION`, `URLS`, etc. so that these can be used in any template, independent of their section.
The global renderer methods for other sections/modules are also exported from [methods.py](main/methods.py) present here, to maintain consistency in rendered information at global level.

The request entry point for this module starts from `/`.
> The SEO based requests & dynamic scripts request for every html template are also being handled here, for instance
> [`/robots.txt`](https://knotters.org/robots.txt) Serves the robots.txt for search engines
> [`/manifest.json`](https://knotters.org/manifest.json) Serves the web-application manifest for installation configuration
> [`/service-worker.js`](https://knotters.org/service-worker.js) Serves the [**service worker**](https://web.dev/service-worker-mindset/)
> [`/scripts/strings.js`](https://knotters.org/scripts/strings.js) Serves STRING global object for all client scripts, mainly to fulfil in-script client translated messages requirements (equivalent to [strings.py](main/strings.py) of backend)
> `/scripts/projects/0.js?id=projectID` The dynamic script for a Quick project's profile. Needs an actual project ID to work.

All future logic & requests independent of any module are expected to be contained in this directory only.

#### [`auth2/`](auth2/)

Although the application itself uses django's account management system with `package:allauth` & `package:allauth_2fa` for extended features, there are still some features related to account management which are not provided by these packages. This `auth2` module was created to serve the exact purpose of handling user account related requests and holding extra information which cannot be achieved using the default modules, like re-authentication, account deactivation/deletion, etc. It is also used/to be used to manage database models for user notification preferences, user demographic details, account related mailing functions, and anything related to or affecting a user's personal account.

The request entry point for this module starts from `/auth`.
> The same entry point here is being used for the `allauth` & `allauth_2fa` packages as well, to maintain consistency in urls related to account management. For instance
> [`/auth/login`](https://knotters.org/auth/login) is handled by `package:allauth`
> [`/auth/two-factor-authenticate`](https://knotters.org/auth/two-factor-authenticate) is handled by `package:allauth`
> [`/auth/`](https://knotters.org/auth/) (accounts homepage) is handled by our `auth2` module itself.

Any account related logic is contained and expected to be contained in this module only.

#### [`people/`](people/)

This module serves the purpose of handling everything related to community of the platform. The name `people` was what community section was called earlier, but later it was renamed to `community`, however the urls and module name continues to remain the same.

The primary requests this module handles is to serve the profile view of any person in community. Apart from this, the actual `class User` database model for users is stored here. Although it may seem that this model fits better in the `auth2/` module, **but changing a model location in a Django project with MongoDB as database, especially involving an important database model like `class User`, brings unintended side-effects for existing records.** Therefore, this `class User` and another related **equally important model `class Profile`** are fated to be contained in this `people/` module, until a migration solution with no side effects is found.

Speaking of `class Profile`, this model is actually used to reference a person from other models which require related user record in their attributes. The Profile model record is created as soon as a User model record (one-to-one relation) is created when a new user creates an account. The reason that Profile model is used for relations of a user with other models is because when a user deletes their account, only their `class User` record is deleted, therefore all associated records of the user which cannot be deleted from the platform for the sake of integrity of other features(results, contribution records, etc.) are retained, as their related `class Profile` record is retained. However, if you are concerned about user's privacy, you can go through the [Knotters Privacy Policy](https://knotters.org/docs/privacypolicy). Roughly speaking, we remove all traces of user identifiable information like email addresses, phone numbers, addresses, name, picture, nickname, etc. when a user deletes their account, and only retain the now became **zombie profile** record to maintain integrity of related records.

Therefore, all user identifiable sensitive information and database models should be put in and related to `class User`, and other records/models which do not require such sensitive information to exist but only user to exist, should relate to `class Profile`.

Also, there can be 4 kinds of users on our platform

- User: A normal user (theme positive) Every user is of this kind for the first time
- Mentor: A mentor user (theme active) A normal user can be promoted by any organization (which they are a part of) as mentor
- Moderator: A moderator user (theme accent) A normal user can be promoted by any organization (which they are a part of) as moderator
- Manager: An organisation account (theme vibrant) Can be converted after signing up as a normal user. Currently user is not allowed to convert themselves, see [#80](https://github.com/knottersbot/knotters/issues/80#issuecomment-1088610164).

More details on the kind of users and their importance will be discussed later on.

The request entry point for this module starts from `/people`.

Apart from all this, other things like profile admiration, blocking, reporting, and relevant community related logic is contained and expected to be contained in this module only.

#### [`projects/`](projects/)

This module serves the purpose of handling everything related to projects section of the platform. The primary purposes are to let a user create a project and host its profile (that's over-simplification).

The main models here are FreeProject (Quick project), Project (verified project), CoreProject (core project). They are used to hold records of the [three categories of projects](https://knotters.org/projects/create/) we have on platform for each user.

There are three kinds of projects allowed on platform

- Quick Project (code name FreeProject, theme positive): Can be created by anyone, doesn't require any moderation. 
- Verified Project (code name Project, theme accent): Can be requested by anyone, requires moderation from an auto assigned moderator (organizations can limit auto assigning to their own moderators)
- Core Project (code name CoreProject, theme vibrant): Can be requested by organizations only, requires moderation from an auto assigned moderator, or a specific moderator, or a moderator from organisation itself.

This section also listens to the contribution events of users from linked GitHub repositories via webhooks and [our own knottersbot](https://github.com/marketplace/knotters-bot), to allot XPs to users based on the same.

The request entry point for this module starts from `/projects`.

Apart from all this, other things like project admiration, posting snapshots, linking assets, and relevant project related logic is contained and expected to be contained in this module only.

#### [`compete/`](compete/)

This module serves the purpose of handling request related to competitions, including but not limited to, participating in a competition, result declaration, certificate allotment and claiming points from a competition.

The main models here are competition submission result. Other models are related to these models for their own specific purposes, related to competitions section of platform.

Competitions can only be created by organizations (managements). Each competition has a moderator, judges, and participants. Moderator and judges are alloted by creators of competitions.

The request entry point for this module starts from `/compete`.

The logic for calculating final scores, points from judgement, generating certificates, and all things related to competitions is contained and expected to be contained in this module.

#### [`moderation/`](moderation/)

This module serves the purpose of handling everything related to moderation.

Allotting allotting a moderator project, moderator to take action on a project or a competition and other kind of moderation related logic is contained and expected to be contained in this module.

Moderator can accept/skip/reject a verified or core project, moderate submissions in assigned competitios etc. via this module.

The request entry point for this module starts from `/moderation`.


#### [`management/`](management/)

This module serves the purpose of handling everything related to organisations, including but not limited to, managing people, promoting or demoting mentors and moderators, creating and managing competitions, declaring results of a competition and allotting certificates.

Organisations can also manage topics, categories and tags created by them or their people, plus they can also create new ones.

The request entry point for this module starts from `/management`.

Any logic for any organization related feature is contained and expected to be contained in this module only.

--

There are, as a matter of fact, other folders as well which are not essential application modules like previous ones, but are crucial their own purposes, explained following

#### [`static/`](static/)

This folder contains and should contain the files/assets which are

- Not a part of the backend application
- Not dynamically generated on runtime like templates (discussed later)
- Are directly accessible by client (therefore no sensitive information should be kept)
- Can be cached by client for offline use

Basically, all the client side scripts, graphics, styles, fonts, and other 3rd party client libraries and assets which will be directly accessed by browser on behalf of the user should be kept in this `static/` folder.

Note that dynamic scripts are not kept in this folder, as they are generated dynamically depending upon request data, thus are not static for all kinds of requests. (Dynamic scripts are discussed in [templates section](#templates)).

All assets in this folder are independent of request data, therefore the name, `static`.

A frontend developer is a person who is expected to work in this folder primarily, for creating client side logic, styles, etc.

Assuming you've the at least some knowledge about service worker technology, and can somewhat understand what [`/service-worker.js`](https://knotters.org/service-worker.js) is serving (which itself is a dynamically generated script), the following things depend on/happen with this `static` directory and its contents

- When a user visits our website for the first time, our service worker gets activated on their browser, in which we have instructed it to fetch all files from `static` folder, and create a static cache database on browser to cache all of its contents (some are excluded, before the service worker is prepared with the final list of all file paths dynamically).
- After the previous step is completed, all requests made by user's browser are handled by service-worker (instructed to do so), and some custom conditions are provider for each request, in which the all requests to contents of this `static` directory are fetched from the browser's cache database, thus speeding up the client side static files loading.
- Now, when a developer at Knotters commits changes a thing or two in `static` folder (a script logic, or a graphic, whatever), a CI deployment procedure is set to run a few steps accordingly in favour of telling client's browser that the user's previous cached database needs to be updated (otherwise user will unknowingly keep using the old static contents from their cache). To achieve this, a `VERSION` tag is being used in the application, which is rendered in service-worker.js as well.
- The relevant CI deployment steps (after running tests, etc) are defined to update that `VERSION` tag first, then copy all contents from `static` folder and place them at `STATIC_ROOT` path, and then compress all of them. Note that the compression & placement of `static` folder contents in `STATIC_ROOT` only takes place automatically in production deployment. For local development environment, the `static` contents are served directly from `static` folder. (However to simulate the production steps you can run `python3 manage.py collectstatic` and `python3 manage.py preparestatics /path/to/new/errors/directory/`)
- The client's browser then detects changes in new service-worker.js file due to changed `VERSION` value, and triggers an update event which is handled by a script [sw.js](static/scripts/sw.js) (which itself is contained in static folder, and is therefore handling the event from cache), which shows a pop-up to user asking to update the application (effectively removing the old static cache and adding the new static contents in cache again).
- Then again, all requests to `static` contents are served directly from our custom cache database in user's browser.

So now you must have got some idea about why static folder is a crucial folder, not only for service static contents and storing client side scripts, but also for effective offlinization of our web-application's assets for better native experience for our users. You may need to understand service worker technology first before getting any hold over this.

Also, you can check the latest version tag at [`/version.txt`](https://knotters.org/version.txt) anytime.

The steps related to version updates are also mentioned in [README](README.md).

The `preparestatics` command is our custom command for compressing static contents, mainly used to serve reduced sized assets in production.

The `VERSION` tag is also used in request paths of static contents to ensure that only the latest content is being served whenever a request comes to server for it. Like, `/static/<VERSION>/scripts/sw.js` will be the final path of this [`sw.js`](static/scripts/sw.js) script file when used in browser by html. The final path is created automatically by backend by attaching the current version in `STATIC_URL` .env path. This `VERSION` value actually comes from [__version__.py](main/__version__.py) which is generated/updated automatically by running `genversion.py` python script.

The CI deployment steps for updates in `static` folder can be seen in [main-client-static.yml](.github/workflows/main-client-static.yml) workflow file. (Other workflow configuration files for different events are also present adjacently).

>In production environment, Django does not serve the contents of `static` (or `STATIC_ROOT`), but only in development environment. So we use our custom server (nginx) to serve our production compressed static files, which effectively serves them in the same manner (but better way) as Django does in development environment (respecting the `/static/<VERSION>/` path)

Phew.

#### [`templates/`](templates/)

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

--

This was an overview for all directories of the project. To make things more clear, all functions, classes etc. have their own description in-code, which works best during suggestions while working on this project in Microsoft VSCode (haven't checked in other code editors)

### User Flow

The previous section roughly explains the code structure of this project. Now, we need to look at the project from user's point of view.
You can, if you want to, read the details page for user oriented explanation of terminologies and features of the platform by visiting [The landing page](https://knotters.org/landing/) of Knotters.

Also, [signing up on Knotters](https://knotters.org/register) by yourself can also help you better understand how things work from user's perspective. Plus, you can get also get perks for yourself just like any other user!

The following steps intend to explain how a user is expected to move around our platform, and therefore will also explain the features of this platform.

## Code Guide

Follow are some specific coding guides for this project, can be used as reference when programming any part.

- Use themes (primary, secondary, tertiary, positive, negative, active, accent, vibrant and their related text themes) for designing elements, rather than creating your own colors. Checkout all themes in theme.css.
  - Projects are primarily associated with positive theme
  - Community is primarily associated with accent theme (the main theme of Knotters)
  - Competitions are primarily associated with active theme
  - Managements are primarily associated with vibrant theme
  - Mentors are primarily associated with active theme (because of involvement in competitions)
  - Moderators are primarily associated with accent theme (because of being a core part of the community)
  - Normal users are primarily associated with positive theme
  - Quick Projects are primarily associated with positive theme (because of normal users)
  - Verified Projects are primarily associated with accent theme (because of involvement of moderators)
  - Core Projects are primarily associated with vibrant theme (because of involvement of managers)

- Some tags have predefined styles, go through all css files for better understanding of existing styles and using them.
  To create a button with positive theme
  ```html
  <button class="positive">Normal postive button</button>
  ```
  The above code will simply create a button with positive theme and adjusted styles.
  ```html
  <button class="big-button accent">Big accent button</button>
  <button class="small negative">Small negative button</button>
  ```
- Many html code elements have shorthands available, which are decided by underlying javascript.
  For example, we use material icons for icons which requires `material-icons` class and `<i></i>` tag.
  But to display an icon in a button,
  ```html
  <button class="active" data-icon="arrow_right">Hello</button>
  ```
  The `data-icon` property is checked by javascript and icon is injected on runtime.
  Similarly there are many more such shorthands available. Note that this `data-icon` is only available for button tags.
  ```html
  <i>arrow_right</i>
  ```
  No need to specify class `material-icons` for `i` tag. You can checkout all such available interpreted shorthands by looking at
  `loadGlobalEventListeners` function in `static/scripts/index.js`, which does the runtime interpretation for these shorthands.

- Various global template context objects are available for every html template, like object `URLS` for all urls in the project. You can see all available global context objects at `main/context_processors.py`.
  Note that the `URLS` object itself is not coming from that file, rather is being generated at global renderer functions in `main/methods.py` for every template.
  Also, the dynamic script `templates/constants.js` makes these global context objects available to all frontend scripts as well.

- Inline scripts are disabled for security reasons. Therefore the concept of dynamic scripts is present in project for scripts depending upon rendered data.
  Try to get scripts code in static folder if possible (dynamic scripts won't work there). To create a new dynamic script file for an html page,
    - Create your script file in `scripts` folder of your module's template folder.
    - In main/strings.py, class Template contains sub-class Script. If the name of your new script file is not already present, then add a new variable in it for that.
    - In main/views.py, a single function to render all dynamic scripts for html files is present. Add your own script's logic in similar fashion as others in that function.
    - Now, at client side, in your html file import the script by using the pre-defined dynamic scripts path and add you own script's name using the global `SCRIPTS` context object.
      Like
      ```html
      <script nonce="{{request.csp_nonce}}" src="{{URLS.SCRIPTS_SUBAPP|params:SUBAPPNAME|params:SCRIPTS.YOUR_SCRIPT_NAME}}?data={{extra_data}}"></script>
      ```
      The `URLS.SCRIPTS_SUBAPP` & `SUBAPPNAME` set the pre-defined path of a dynamic scripts for any html page of any module. The value of `SCRIPTS.YOUR_SCRIPT_NAME` is coming directly from that `class Script`.
      The `data={{extra_data}}` can be any data you need to use for dynamicity of your script in the script rendering function.
      For example
      ```html
      <script nonce="{{request.csp_nonce}}" src="{{URLS.SCRIPTS_SUBAPP|params:SUBAPPNAME|params:SCRIPTS.PROFILE}}?id={{person.id}}"></script>
      ```
      The above script import example can be found at the bottom of `templates/people/profile.html`.

You can start contribution by going through the [issues](https://github.com/knottersbot/knotters/issues) and working upon them as per your knowledge.
In doubt, you can always reach out the maintainers of this project.

## Recommendations

- Always document your code as much as possible. Every function, class, Global object, or anything worth documenting created by you should be documented by you too. Follow the pattern being followed in existing source code for documentation.

- Write tests for everything you create, especially for the request handling functions.

- Avoid changing database model names once deployed, to avoid problems related to existing records.

- Always create a separate branch for any new task, and always create it from the beta branch.

- Always create a pull request from your branch to beta branch. No changes should be made on main branch directly.

- Updates on beta branch are always deployed on beta.knotters.org

- Before creating anything new, always check whether something already exists for that or not. Especially for frontend part, try to reuse the defined style classes and design patterns to maintain consistency in UI and UX as much as possible.

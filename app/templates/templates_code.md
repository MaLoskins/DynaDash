# CODEBASE

## Directory Tree:

### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates

```
/mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates
├── .gitkeep
├── auth/
│   ├── .gitkeep
│   ├── change_password.html
│   ├── login.html
│   ├── profile.html
│   └── register.html
├── errors/
│   ├── 400.html
│   ├── 401.html
│   ├── 403.html
│   ├── 404.html
│   ├── 500.html
│   └── base_error.html
├── shared/
│   ├── .gitkeep
│   ├── base.html
│   ├── error.html
│   └── index.html
└── visual/
    ├── .gitkeep
    ├── generate.html
    ├── index.html
    ├── share.html
    ├── view.html
    └── welcome.html
```

## Code Files


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/.gitkeep

```
# This file is intentionally left empty to ensure the templates directory is included in the Git repository.
# The templates directory is used to store Jinja2 templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/.gitkeep

```
# This file is intentionally left empty to ensure the auth directory is included in the Git repository.
# The auth directory is used to store authentication-related templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/change_password.html

```
{% extends "shared/base.html" %}

{% block title %}Change Password - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div class="shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6">
                <h3 class="text-lg leading-6 font-medium">
                    Change Password
                </h3>
                <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                    Update your account password.
                </p>
            </div>
            <div class="border-t border-border-color px-4 py-5 sm:px-6">
                <form action="{{ url_for('auth.change_password') }}" method="POST">
                    {{ form.hidden_tag() }}
                    
                    <div class="mb-4">
                        <label for="current_password" class="block text-sm font-medium">
                            {{ form.current_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.current_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.current_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.current_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label for="new_password" class="block text-sm font-medium">
                            {{ form.new_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.new_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.new_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.new_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="mb-6">
                        <label for="confirm_new_password" class="block text-sm font-medium">
                            {{ form.confirm_new_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.confirm_new_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.confirm_new_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.confirm_new_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="flex justify-end">
                        <a href="{{ url_for('auth.profile') }}" class="py-2 px-4 border border-border-color rounded-md shadow-sm text-sm font-medium hover:bg-highlight focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary mr-2">
                            Cancel
                        </a>
                        {{ form.submit(class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary") }}
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/login.html

```
{% extends "shared/base.html" %}

{% block title %}Login - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-card-bg p-8 rounded-lg shadow-md border border-border-color">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold">
                Login to DynaDash
            </h2>
            <p class="mt-2 text-center text-sm">
                Or
                <a href="{{ url_for('auth.register') }}" class="font-medium hover:text-magenta-secondary">
                    create a new account
                </a>
            </p>
        </div>
        <form class="mt-8 space-y-6" action="{{ url_for('auth.login') }}" method="POST">
            {{ form.hidden_tag() }}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="email" class="sr-only">Email address</label>
                    {{ form.email(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-t-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Email address") }}
                    {% if form.email.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.email.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    {{ form.password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-b-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Password") }}
                    {% if form.password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    {{ form.remember_me(class="h-4 w-4 focus:ring-magenta-primary border rounded") }}
                    <label for="remember_me" class="ml-2 block text-sm">
                        Remember me
                    </label>
                </div>
            </div>

            <div>
                {{ form.submit(class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2") }}
            </div>
        </form>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/profile.html

```
{% extends "shared/base.html" %}

{% block title %}Profile - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
                <div>
                    <h3 class="text-lg leading-6 font-medium">
                        User Profile
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm">
                        Your personal information and account details.
                    </p>
                </div>
                <a href="{{ url_for('auth.change_password') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm">
                    Change Password
                </a>
            </div>
            <div class="border-t border-border-color">
                <dl>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt class="text-sm font-medium text-text-secondary">
                            Full name
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.name }}
                        </dd>
                    </div>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 border-t border-border-color">
                        <dt class="text-sm font-medium text-text-secondary">
                            Email address
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.email }}
                        </dd>
                    </div>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 border-t border-border-color">
                        <dt class="text-sm font-medium text-text-secondary">
                            Account created
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.created_at.strftime('%B %d, %Y') }}
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
        
        <div class="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div class="shadow overflow-hidden sm:rounded-lg">
                <div class="px-4 py-5 sm:px-6">
                    <h3 class="text-lg leading-6 font-medium">
                        My Datasets
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                        Summary of your uploaded datasets.
                    </p>
                </div>
                <div class="border-t border-border-color px-4 py-5 sm:px-6">
                    <div class="text-center">
                        <a href="{{ url_for('data.index') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary">
                            View All Datasets
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="shadow overflow-hidden sm:rounded-lg">
                <div class="px-4 py-5 sm:px-6">
                    <h3 class="text-lg leading-6 font-medium">
                        My Visualizations
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                        Summary of your generated visualizations.
                    </p>
                </div>
                <div class="border-t border-border-color px-4 py-5 sm:px-6">
                    <div class="text-center">
                        <a href="{{ url_for('visual.index') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary">
                            View All Visualizations
                        </a>
                    </div>
                </div>
            </div>
            
            <a href="#" onclick="confirmAndSubmit()" 
               class="justify-self-start inline-flex items-center px-2 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm">
                Delete Account
            </a>

            <!-- hidden form (with CSRF) -->
            <form id="delete-account-form"
                action="{{ url_for('auth.delete_account') }}"
                method="POST"
                style="display: none;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            </form>

        </div>
    </div>
</div>

<!-- Account Delete Confirmation Modal -->
<div id="delete-account-modal"
     class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
  <div class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
    <h3 class="text-xl font-bold text-gray-800 mb-4">Confirm Deletion</h3>
    <p class="text-gray-600 mb-6">
      Are you sure you want to delete your account? All related data will be erased. This cannot be undone.
    </p>
    <div class="flex justify-end space-x-4">
      <button id="cancel-delete-account"
              class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition">
        Cancel
      </button>
      <button id="confirm-delete-account"
              class="bg-pink-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition">
        Delete
      </button>
    </div>
  </div>
</div>

<script  src="{{ url_for('static', filename='js/profile.js') }}" defer></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/register.html

```
{% extends "shared/base.html" %}

{% block title %}Register - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-card-bg p-8 rounded-lg shadow-md border border-border-color">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold">
                Create an Account
            </h2>
            <p class="mt-2 text-center text-sm">
                Or
                <a href="{{ url_for('auth.login') }}" class="font-medium hover:text-magenta-secondary">
                    sign in to your existing account
                </a>
            </p>
        </div>
        <form class="mt-8 space-y-6" action="{{ url_for('auth.register') }}" method="POST">
            {{ form.hidden_tag() }}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="name" class="sr-only">Name</label>
                    {{ form.name(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-t-md focus:outline-none focus:z-10 sm:text-sm", placeholder="User name") }}
                    {% if form.name.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.name.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="email" class="sr-only">Email address</label>
                    {{ form.email(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Email address") }}
                    {% if form.email.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.email.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    {{ form.password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Password") }}
                    {% if form.password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="confirm_password" class="sr-only">Confirm Password</label>
                    {{ form.confirm_password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Confirm Password") }}
                    {% if form.confirm_password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.confirm_password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>

            <div>
                {{ form.submit(class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2") }}
            </div>
        </form>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/400.html

```
{% extends "errors/base_error.html" %}

{% set code = 400 %}
{% set title = "Bad Request" %}
{% set message = "The server could not understand your request. Please check your input and try again." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/401.html

```
{% extends "errors/base_error.html" %}

{% set code = 401 %}
{% set title = "Unauthorized" %}
{% set message = "You need to be authenticated to access this resource. Please log in and try again." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/403.html

```
{% extends "errors/base_error.html" %}

{% set code = 403 %}
{% set title = "Forbidden" %}
{% set message = "You don't have permission to access this resource. Please check your credentials or contact the administrator." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/404.html

```
{% extends "errors/base_error.html" %}

{% set code = 404 %}
{% set title = "Page Not Found" %}
{% set message = "The page you are looking for does not exist. It might have been moved or deleted." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/500.html

```
{% extends "errors/base_error.html" %}

{% set code = 500 %}
{% set title = "Internal Server Error" %}
{% set message = "Something went wrong on our end. Please try again later or contact support if the problem persists." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/base_error.html

```
{% extends "shared/base.html" %}

{% block title %}{{ code }} {{ title }} - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 text-center">
        <div>
            <h1 class="text-9xl font-extrabold text-blue-600">{{ code }}</h1>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                {{ title }}
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                {{ message }}
            </p>
        </div>
        <div>
            <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('auth.login') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Go to Home
            </a>
        </div>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/.gitkeep

```
# This file is intentionally left empty to ensure the shared directory is included in the Git repository.
# The shared directory is used to store shared templates that are used across multiple parts of the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/base.html

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DynaDash{% endblock %}</title>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/2.3.0/purify.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">

    {% block head_scripts %}
    {% if current_user.is_authenticated %}
    <script>
        window.dynadash_current_user_id = {{ current_user.id | tojson }};
    </script>
    {% else %}
    <script>
        window.dynadash_current_user_id = null;
    </script>
    {% endif %}
    {% endblock %}
    
    {% block styles %}{% endblock %}
</head>
<body class="min-h-screen flex flex-col">
    <nav class="fixed top-0 left-0 w-full text-white shadow-md z-50 h-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('visual.welcome') }}" class="font-bold text-xl">
                            DynaDash
                        </a>
                    </div>
                {% if current_user.is_authenticated %}
                   <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                    <a href="{{ url_for('visual.index') }}"
                       class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('visual') %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent hover:border-gray-300{% endif %}">
                          Visualizations
                    </a>
                    {# Use the new context function to check if data blueprint routes exist #}
                    {% if data_blueprint_exists_and_has_route('index') %}
                    <a href="{{ url_for('data.index') }}"
                      class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent hover:border-gray-300{% endif %}">
                        Datasets 
                    </a>
                    {% endif %}
                    {% if data_blueprint_exists_and_has_route('upload') %}
                    <a href="{{ url_for('data.upload') }}"
                        class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint == 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent hover:border-gray-300{% endif %}">
                         Upload   
                    </a>
                    {% endif %}
                   </div>
                {% endif %}
                </div>
                <div class="hidden sm:ml-6 sm:flex sm:items-center">
                    {% if current_user.is_authenticated %}
                    <div class="ml-3 relative">
                        <div class="flex items-center">
                            <span class="mr-2">{{ current_user.name }}</span>
                            <div class="relative">
                                <button type="button" id="user-menu-button" class="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2">
                                    <span class="sr-only">Open user menu</span>
                                    <div class="h-8 w-8 rounded-full flex items-center justify-center" style="background-color: var(--magenta-primary); color: var(--text-color);">
                                        {{ current_user.name[0] }}
                                    </div>
                                </button>
                            </div>
                            <div id="user-menu" class="hidden absolute right-0 top-full mt-2 w-48 bg-card-bg border border-border-color rounded-md shadow-xl z-50 py-1 focus:outline-none ring-1 ring-black ring-opacity-5" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
                                <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-sm text-text-color hover:bg-highlight" role="menuitem">Your Profile</a>
                                <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-sm text-text-color hover:bg-highlight" role="menuitem">Change Password</a>
                                <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-sm text-text-color hover:bg-highlight" role="menuitem">Sign out</a>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex space-x-4">
                        <a href="{{ url_for('auth.login') }}" class="text-text-color hover:text-magenta-light px-3 py-2 rounded-md text-sm font-medium">Login</a>
                        <a href="{{ url_for('auth.register') }}" class="bg-magenta-primary hover:bg-magenta-dark text-white px-3 py-2 rounded-md text-sm font-medium">Register</a>
                    </div>
                    {% endif %}
                </div>
                <div class="-mr-2 flex items-center sm:hidden">
                    <button type="button" id="mobile-menu-button" class="inline-flex items-center justify-center p-2 rounded-md text-text-color hover:text-white hover:bg-highlight focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white">
                        <span class="sr-only">Open main menu</span>
                        <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div id="mobile-menu" class="hidden sm:hidden">
            <div class="pt-2 pb-3 space-y-1">
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('visual.index') }}" class="{% if request.endpoint and request.endpoint == 'visual.index' %}bg-highlight text-white{% else %}text-text-color-muted hover:bg-highlight-hover hover:text-white{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Visualizations
                </a>
                {% if data_blueprint_exists_and_has_route('index') %}
                <a href="{{ url_for('data.index') }}" class="{% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}bg-highlight text-white{% else %}text-text-color-muted hover:bg-highlight-hover hover:text-white{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Datasets
                </a>
                {% endif %}
                {% if data_blueprint_exists_and_has_route('upload') %}
                <a href="{{ url_for('data.upload') }}" class="{% if request.endpoint and request.endpoint == 'data.upload' %}bg-highlight text-white{% else %}text-text-color-muted hover:bg-highlight-hover hover:text-white{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Upload
                </a>
                {% endif %}
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="text-text-color-muted hover:bg-highlight-hover hover:text-white block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Login
                </a>
                <a href="{{ url_for('auth.register') }}" class="text-text-color-muted hover:bg-highlight-hover hover:text-white block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Register
                </a>
                {% endif %}
            </div>
            {% if current_user.is_authenticated %}
            <div class="pt-4 pb-3 border-t border-border-color">
                <div class="flex items-center px-4">
                    <div class="flex-shrink-0">
                        <div class="h-10 w-10 rounded-full flex items-center justify-center" style="background-color: var(--magenta-primary); color: var(--text-color);">
                            {{ current_user.name[0] }}
                        </div>
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium text-text-color">{{ current_user.name }}</div>
                        <div class="text-sm font-medium text-text-secondary">{{ current_user.email }}</div>
                    </div>
                </div>
                <div class="mt-3 space-y-1">
                    <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-base font-medium text-text-color-muted hover:bg-highlight-hover hover:text-white rounded-md">
                        Your Profile
                    </a>
                    <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-base font-medium text-text-color-muted hover:bg-highlight-hover hover:text-white rounded-md">
                        Change Password
                    </a>
                    <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-base font-medium text-text-color-muted hover:bg-highlight-hover hover:text-white rounded-md">
                        Sign out
                    </a>
                </div>
            </div>
            {% endif %}
        </div>
    </nav>

    <div class="flash-messages">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">
                        {{ message }}
                        <button type="button" class="close-flash ml-2">×</button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <main class="flex-grow pt-16">
        {% block content %}{% endblock %}
    </main>

    <footer class="py-4 mt-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center">
                <div class="text-sm text-text-secondary">
                    © 2025 DynaDash. All rights reserved.
                </div>
                <div class="text-sm text-text-secondary">
                    Created by Matthew Haskins, Leo Chen, Jonas Liu, Ziyue Xu
                </div>
            </div>
        </div>
    </footer>
    
    <script src="{{ url_for('static', filename='js/common.js') }}" defer></script>

    {% block scripts %}{% endblock %}
</body>
</html>
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/error.html

```
{% extends "shared/base.html" %}

{% block title %}Error {{ error_code }} - DynaDash{% endblock %}

{% block content %}
<div class="flex flex-col items-center justify-center py-16">
    <div class="text-red-500 text-6xl font-bold mb-4">{{ error_code }}</div>
    <h1 class="text-3xl font-bold text-gray-800 mb-6">{{ error_message }}</h1>
    
    <p class="text-gray-600 mb-8 text-center max-w-lg">
        {% if error_code == 404 %}
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
        {% elif error_code == 403 %}
        You don't have permission to access this resource.
        {% elif error_code == 500 %}
        Something went wrong on our end. Please try again later.
        {% else %}
        An error occurred while processing your request.
        {% endif %}
    </p>
    
    <div class="flex space-x-4">
        <a href="{{ url_for('visual.index') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300">
            Go to Home
        </a>
        <button onclick="window.history.back()" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition duration-300">
            Go Back
        </button>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/index.html

```
{% extends "shared/base.html" %}

{% block title %}DynaDash - Dynamic Data Analytics{% endblock %}

{% block content %}
<div class="flex flex-col items-center justify-center py-12">
    <h1 class="text-4xl font-bold text-blue-600 mb-6">Welcome to DynaDash</h1>
    <p class="text-xl text-gray-700 mb-8 text-center max-w-3xl">
        A web-based data-analytics platform that lets you upload datasets, 
        receive automated visualizations powered by Claude AI, and share insights with your team.
    </p>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl mb-12">
        <!-- Feature 1 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-upload"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Upload Datasets</h3>
            <p class="text-gray-600">
                Securely upload your CSV or JSON datasets and preview them instantly.
            </p>
        </div>
        
        <!-- Feature 2 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-chart-bar"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">AI-Powered Visualizations</h3>
            <p class="text-gray-600">
                Get automated exploratory analyses & visualizations generated by Claude AI.
            </p>
        </div>
        
        <!-- Feature 3 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-cubes"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Manage Your Gallery</h3>
            <p class="text-gray-600">
                Curate, annotate & manage visualizations in your personal gallery.
            </p>
        </div>
        
        <!-- Feature 4 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-share-alt"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Share Insights</h3>
            <p class="text-gray-600">
                Selectively share chosen datasets or charts with nominated peers.
            </p>
        </div>
    </div>
    
    {% if not current_user.is_authenticated %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('auth.register') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
            Register Now
        </a>
        <a href="{{ url_for('auth.login') }}" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-6 rounded-lg transition duration-300">
            Login
        </a>
    </div>
    {% else %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('data.upload') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
            Upload Dataset
        </a>
        <a href="{{ url_for('visual.index') }}" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-6 rounded-lg transition duration-300">
            View Visualizations
        </a>
    </div>
    {% endif %}
</div>

<!-- How It Works Section -->
<div class="bg-gray-50 py-16">
    <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">1. Upload Your Data</h3>
                <p class="text-gray-600 mb-4">
                    Upload your CSV or JSON datasets securely to the platform. 
                    Our system validates your data and provides an instant preview.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>Support for CSV and JSON formats</li>
                    <li>Secure file handling</li>
                    <li>Instant data preview</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Upload Interface</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 md:order-2 mb-8 md:mb-0 md:pl-8">
                <h3 class="text-2xl font-semibold mb-4">2. Generate Visualizations</h3>
                <p class="text-gray-600 mb-4">
                    Our AI-powered system analyzes your data and generates meaningful visualizations 
                    automatically using Anthropic's Claude API.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>AI-powered data analysis</li>
                    <li>Multiple chart types</li>
                    <li>Real-time progress tracking</li>
                </ul>
            </div>
            <div class="md:w-1/2 md:order-1">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Visualization Process</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">3. Share and Collaborate</h3>
                <p class="text-gray-600 mb-4">
                    Curate your visualizations in a personal gallery and selectively share them 
                    with team members for collaboration.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>Fine-grained access control</li>
                    <li>Personal visualization gallery</li>
                    <li>Team collaboration features</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Sharing Interface</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<!-- Font Awesome for icons -->
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/.gitkeep

```
# This file is intentionally left empty to ensure the visual directory is included in the Git repository.
# The visual directory is used to store visualization-related templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/generate.html

```
{% extends "shared/base.html" %}

{% block title %}Generate Dashboard - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-gray-800">Generate Dashboard</h1>
            {# Ensure data.view exists or provide a fallback #}
            <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else url_for('visual.index') }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Dataset
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Dataset Info -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Dataset Details</h2>
                    </div>
                    <div class="p-4">
                        <h3 class="font-medium text-gray-200 mb-1">{{ dataset.original_filename }}</h3>
                        <p class="text-sm text-gray-500 mb-4">
                            {{ dataset.file_type.upper() }} • {{ dataset.n_rows }} rows • {{ dataset.n_columns }} columns
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Uploaded:</span> {{ dataset.uploaded_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Visibility:</span> 
                            <span class="{{ 'text-green-600' if dataset.is_public else 'text-gray-800' }}">
                                {{ 'Public' if dataset.is_public else 'Private' }}
                            </span>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Dashboard Form -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Dashboard Options</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.generate', dataset_id=dataset.id) }}" id="dashboard-form">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-4">
                                <label for="title" class="block text-sm font-medium text-gray-700">
                                    {{ form.title.label }}
                                </label>
                                <div class="mt-1">
                                    {{ form.title(class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md") }}
                                    {% if form.title.errors %}
                                        <div class="text-red-500 text-xs mt-1">
                                            {% for error in form.title.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="description" class="block text-sm font-medium text-gray-700">
                                    {{ form.description.label }}
                                </label>
                                <div class="mt-1">
                                    {{ form.description(class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md", rows=3, placeholder="Describe what insights you're looking for or what aspects of the data you want to highlight...") }}
                                    {% if form.description.errors %}
                                        <div class="text-red-500 text-xs mt-1">
                                            {% for error in form.description.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    Adding a descriptive explanation of your data and what insights you're looking for will help generate more relevant visualizations.
                                </p>
                            </div>
                            
                            <div class="mb-6">
                                <div class="bg-blue-50 border border-blue-200 rounded p-3">
                                    <span class="text-blue-800 text-sm">
                                        <strong>Note:</strong> Claude will analyze your dataset and automatically create a fully interactive dashboard with multiple visualizations. This process may take up to 60-90 seconds for larger datasets.
                                    </span>
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {{ form.submit(class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500", value="Generate Dashboard", id="submit-button") }}
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Processing Modal -->
        <div id="processing-modal" class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
            <div class="bg-card-bg rounded-lg shadow-lg p-6 max-w-md w-full border border-border-color">
                <h3 class="text-xl font-bold text-text-color mb-4">Generating Dashboard</h3>
                <div class="mb-4">
                    <div class="progress-container">
                        <div id="progress-bar" style="width: 0%"></div>
                    </div>
                    <p id="progress-label" class="text-sm text-text-secondary mt-2">Initializing...</p>
                </div>
                <div class="text-text-secondary text-sm">
                    <p class="mb-2">Claude is analyzing your data and creating a custom dashboard. This may take 60-90 seconds to complete.</p>
                    <div id="steps-container" class="border border-border-color rounded p-2 mt-3">
                        <p class="text-xs text-text-tertiary mb-1">Current progress:</p>
                        <ul class="text-xs space-y-1">
                            <li id="step-1" class="flex items-center">
                                <span class="step-indicator" id="step-1-indicator"></span> 
                                <span>Preparing dataset and analyzing structure</span>
                            </li>
                            <li id="step-2" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-2-indicator"></span> 
                                <span>Identifying key data relationships</span>
                            </li>
                            <li id="step-3" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-3-indicator"></span> 
                                <span>Generating dashboard layout</span>
                            </li>
                            <li id="step-4" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-4-indicator"></span> 
                                <span>Creating visualizations</span>
                            </li>
                            <li id="step-5" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-5-indicator"></span> 
                                <span>Finalizing and saving dashboard</span>
                            </li>
                        </ul>
                    </div>
                </div>
                <div id="error-message-modal" class="mt-4 p-3 bg-red-100 border border-red-300 rounded text-red-700 text-sm hidden">
                    An error occurred. Please try again or contact support if the problem persists.
                </div>
            </div>
        </div>

    </div>
</div>
{% endblock %}

{% block scripts %}
{# visual_generate.js is NOT for this page, it's for view.html #}
{# Add specific JS for this page if needed, e.g. for handling form submission with SocketIO progress #}
<script>
document.addEventListener("DOMContentLoaded", function () {
    const dashboardForm = document.getElementById('dashboard-form');
    const processingModal = document.getElementById('processing-modal');
    const progressBar = document.getElementById('progress-bar');
    const progressLabel = document.getElementById('progress-label');
    const errorMessageModal = document.getElementById('error-message-modal');
    
    const steps = {
        1: { percent: 10, message: "Preparing dataset and analyzing structure", indicator: "step-1-indicator", text_el_id: "step-1" },
        2: { percent: 30, message: "Identifying key data relationships", indicator: "step-2-indicator", text_el_id: "step-2" },
        3: { percent: 50, message: "Generating dashboard layout", indicator: "step-3-indicator", text_el_id: "step-3" },
        4: { percent: 70, message: "Creating visualizations", indicator: "step-4-indicator", text_el_id: "step-4" },
        5: { percent: 90, message: "Finalizing and saving dashboard", indicator: "step-5-indicator", text_el_id: "step-5" }
    };

    function updateStepIndicator(currentPercent) {
        for (const stepNum in steps) {
            const step = steps[stepNum];
            const indicatorEl = document.getElementById(step.indicator);
            const textEl = document.getElementById(step.text_el_id);
            if (indicatorEl && textEl) {
                if (currentPercent >= step.percent) {
                    indicatorEl.classList.remove('bg-gray-300');
                    indicatorEl.classList.add('step-completed'); // Or 'step-active' if it's the current one
                    textEl.classList.remove('text-text-tertiary');
                    textEl.classList.add('text-text-color');
                } else {
                     indicatorEl.classList.remove('step-completed', 'step-active');
                     indicatorEl.classList.add('bg-gray-300');
                     textEl.classList.remove('text-text-color');
                     textEl.classList.add('text-text-tertiary');
                }
            }
        }
    }


    if (dashboardForm && processingModal && progressBar && progressLabel) {
        dashboardForm.addEventListener('submit', function(event) {
            // Client-side validation can be added here if needed before showing modal
            processingModal.classList.remove('hidden');
            progressBar.style.width = '0%';
            progressLabel.textContent = 'Initializing...';
            if(errorMessageModal) errorMessageModal.classList.add('hidden'); // Clear previous errors
            updateStepIndicator(0); // Reset step indicators

            // SocketIO event listeners are now in common.js
            // This script just needs to trigger the submission
        });
    }

    // This part will be handled by common.js now
    // const socket = io(); // Assuming common.js initializes socket if user is authenticated
    // if (typeof socket !== 'undefined') { // Check if socket was initialized
    //     socket.on('progress_update', function(data) {
    //         if (progressBar && progressLabel) {
    //             progressBar.style.width = data.percent + '%';
    //             progressLabel.textContent = data.message;
    //             updateStepIndicator(data.percent);
    //         }
    //     });

    //     socket.on('processing_complete', function(data) {
    //         if (progressBar && progressLabel) {
    //             progressBar.style.width = '100%';
    //             progressLabel.textContent = 'Dashboard completed! Redirecting...';
    //             updateStepIndicator(100);
    //         }
    //         if (data && data.redirect_url) {
    //             window.location.href = data.redirect_url;
    //         } else {
    //             // Fallback if no redirect URL is provided
    //             setTimeout(() => { processingModal.classList.add('hidden'); }, 2000);
    //         }
    //     });

    //     socket.on('processing_error', function(data) {
    //         if (processingModal && errorMessageModal && progressLabel) {
    //             progressLabel.textContent = 'Error occurred.';
    //             errorMessageModal.textContent = 'Error: ' + data.message;
    //             errorMessageModal.classList.remove('hidden');
    //             // Optionally hide modal after a delay or provide a close button
    //             // setTimeout(() => { processingModal.classList.add('hidden'); }, 5000);
    //         } else {
    //             alert('Error: ' + data.message); // Fallback
    //         }
    //     });
    // }
});
</script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/index.html

```
{% extends "shared/base.html" %}

{% block title %}My Visualizations - DynaDash{% endblock %}

{% block content %}
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/share.html

```
{% extends "shared/base.html" %}

{% block title %}Share Visualization - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-3xl font-bold text-gray-800">Share Visualization</h1>
            <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Visualization
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Visualization Info -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Visualization Details</h2>
                    </div>
                    <div class="p-4">
                        <h3 class="font-medium text-gray-200 mb-1">{{ visualisation.title }}</h3>
                        {% if visualisation.description %}
                            <p class="text-sm text-gray-500 mb-4">{{ visualisation.description }}</p>
                        {% endif %}
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Created:</span> {{ visualisation.created_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Dataset:</span> {{ dataset.original_filename }}
                        </p>
                        
                        <div class="mt-4 p-2 bg-gray-50 rounded">
                            <div class="text-xs text-gray-500 mb-1">Preview:</div>
                            <div class="h-32 flex items-center justify-center bg-gray-100 rounded">
                                <span class="text-gray-400 text-sm">Visualization Preview</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Share Form -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Share with Users</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.share', id=visualisation.id) }}">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-6">
                                <label for="user_id" class="block text-gray-700 text-sm font-bold mb-2">
                                    {{ form.user_id.label }}
                                </label>
                                {{ form.user_id(class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline") }}
                                {% if form.user_id.errors %}
                                    <div class="text-red-500 text-xs mt-1">
                                        {% for error in form.user_id.errors %}
                                            <span>{{ error }}</span>
                                        {% endfor %}
                                    </div>
                                {% endif %}
                            </div>
                            
                            <div class="flex justify-end">
                                {{ form.submit(class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-300") }}
                            </div>
                        </form>
                        
                        <div class="mt-8">
                            <h3 class="text-lg font-medium text-gray-700 mb-4">Currently Shared With</h3>
                            
                            {% if shared_with %}
                                <div class="bg-white border rounded-lg overflow-hidden">
                                    <table class="min-w-full divide-y divide-gray-200">
                                        <thead class="bg-gray-50">
                                            <tr>
                                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    User
                                                </th>
                                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody class="bg-white divide-y divide-gray-200">
                                            {% for user in shared_with %}
                                                <tr>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <div class="flex items-center">
                                                            <div class="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                                                                <span class="text-gray-500">{{ user.name[0] }}</span>
                                                            </div>
                                                            <div class="ml-4">
                                                                <div class="text-sm font-medium text-gray-900">
                                                                    {{ user.name }}
                                                                </div>
                                                                <div class="text-sm text-gray-500">
                                                                    {{ user.email }}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        <form action="{{ url_for('visual.unshare', id=visualisation.id, user_id=user.id) }}" method="POST" class="inline">
                                                            <button type="submit" class="text-red-600 hover:text-red-900">
                                                                Remove
                                                            </button>
                                                        </form>
                                                    </td>
                                                </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="bg-gray-50 rounded-lg p-6 text-center">
                                    <div class="text-gray-400 text-4xl mb-3">
                                        <i class="fas fa-users-slash"></i>
                                    </div>
                                    <p class="text-gray-600">
                                        This visualization is not shared with anyone yet.
                                    </p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 class="text-lg font-semibold text-blue-800 mb-2">Sharing Information</h3>
                    <ul class="list-disc list-inside text-blue-700 space-y-1">
                        <li>Shared users can view but not modify your visualization</li>
                        <li>You can revoke access at any time</li>
                        <li>Users will be notified when you share a visualization with them</li>
                        <li>The dataset used to create this visualization will also be accessible to shared users</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/view.html

```
{% extends "shared/base.html" %}

{% block title %}{{ visualisation.title }} - DynaDash{% endblock %}

{% block head_scripts %} {# Changed from 'head' to 'head_scripts' to match base.html #}
    {{ super() }}
    <style>
        .dashboard-frame { width: 100%; height: 800px; min-height: 800px; border: none; background-color: white; }
        .dashboard-frame canvas { max-width: 100%; }
        .dashboard-container { height: auto; min-height: 800px; position: relative; width: 100%; }
        .fullscreen-toggle { position: absolute; top: 10px; right: 10px; z-index: 100; padding: 5px 10px; background-color: rgba(0,0,0,0.5); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .fullscreen-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background-color: white; display: none; }
        .fullscreen-container .dashboard-frame { height: 100%; width: 100%; }
        .fullscreen-container .fullscreen-toggle { top: 20px; right: 20px; }
        .dashboard-error { padding: 20px; text-align: center; background-color: #fff3f3; border: 1px solid #ffcaca; border-radius: 8px; margin: 20px 0; }
        .dashboard-error h3 { color: #e74c3c; margin-bottom: 10px; }
        .dashboard-error p { margin-bottom: 15px; }
        .dashboard-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; }
        .spinner { border: 4px solid rgba(0, 0, 0, 0.1); width: 40px; height: 40px; border-radius: 50%; border-left-color: #3498db; animation: spin 1s ease infinite; margin-bottom: 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .lg\:col-span-3 { width: 100%; }
        /* Ensure no default margin/padding in iframe body */
        /* These styles will be applied by prepare_dashboard_template_html if needed */
        /* .dashboard-frame html, .dashboard-frame body { height: 100%; width: 100%; margin: 0; padding: 0; overflow: auto; } */
    </style>
    {# Inject actual dataset JSON into a global JS variable for the dashboard renderer #}
    <script>
        window.dynadashDatasetJson = {{ actual_dataset_json|safe }};
        window.dynadashDashboardTemplateHtml = {{ dashboard_template_html|tojson|safe }};
    </script>
{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold text-text-color">{{ visualisation.title }}</h1>
                {% if visualisation.description %}
                    <p class="text-text-secondary mt-1">{{ visualisation.description }}</p>
                {% endif %}
            </div>
            <div class="flex space-x-3">
                <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left mr-1"></i> Back to Dashboards
                </a>
                
                {% if dataset.user_id == current_user.id %}
                    <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn bg-green-600 hover:bg-green-700">
                        <i class="fas fa-share-alt mr-1"></i> Share
                    </a>
                    
                    <form action="{{ url_for('visual.delete', id=visualisation.id) }}" method="POST" class="inline">
                        {# CSRF token should be included if CSRFProtect is active for POSTs #}
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="btn bg-red-600 hover:bg-red-700" 
                                onclick="return confirm('Are you sure you want to delete this dashboard? This action cannot be undone.');">
                            <i class="fas fa-trash-alt mr-1"></i> Delete
                        </button>
                    </form>
                {% endif %}
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="lg:col-span-1">
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden mb-6 border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard Details</h2>
                    </div>
                    <div class="p-4">
                        <ul class="space-y-3">
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Created:</span>
                                <span class="font-medium text-text-color-muted">{{ visualisation.created_at.strftime('%b %d, %Y') }}</span>
                            </li>
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Dataset:</span>
                                <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="font-medium text-magenta-primary hover:text-magenta-light">
                                    {{ dataset.original_filename }}
                                </a>
                            </li>
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Owner:</span>
                                <span class="font-medium text-text-color-muted">{{ dataset.owner.name }}</span>
                            </li>
                        </ul>
                    </div>
                </div>
                
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Actions</h2>
                    </div>
                    <div class="p-4 space-y-3">
                        {% if dataset.user_id == current_user.id %}
                            <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn bg-green-600 hover:bg-green-700 text-white w-full text-center">
                                <i class="fas fa-share-alt mr-1"></i> Share Dashboard
                            </a>
                        {% endif %}
                        
                        <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="btn bg-accent-blue hover:bg-accent-blue-dark text-white w-full text-center">
                            <i class="fas fa-database mr-1"></i> View Dataset
                        </a>
                        
                        <button id="fullscreen-btn" class="btn bg-accent-purple hover:bg-accent-purple-dark text-white w-full text-center">
                            <i class="fas fa-expand mr-1"></i> Fullscreen Mode
                        </button>
                        
                        <button id="download-btn-dashboard" class="btn bg-gray-500 hover:bg-gray-600 text-white w-full text-center">
                            <i class="fas fa-download mr-1"></i> Download HTML
                        </button>
                        
                        <button id="refresh-btn-dashboard" class="btn bg-accent-cyan hover:bg-accent-cyan-dark text-white w-full text-center">
                            <i class="fas fa-sync-alt mr-1"></i> Refresh Dashboard
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="lg:col-span-3">
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden w-full border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard</h2>
                    </div>
                    <div class="dashboard-container">
                        <div id="dashboard-loading" class="dashboard-loading">
                            <div class="spinner"></div>
                            <p class="text-text-secondary">Loading dashboard...</p>
                        </div>
                        
                        <div id="dashboard-error" class="dashboard-error" style="display: none;">
                            <h3><i class="fas fa-exclamation-circle"></i> Dashboard Display Issue</h3>
                            <p class="text-text-secondary">There was a problem displaying the dashboard. This may be due to browser security restrictions or a temporary issue.</p>
                            <div>
                                <button id="reload-dashboard-btn" class="btn bg-accent-blue hover:bg-accent-blue-dark text-white">
                                    <i class="fas fa-sync-alt mr-1"></i> Try Again
                                </button>
                                <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="btn btn-secondary ml-2">
                                    <i class="fas fa-arrow-right mr-1"></i> Reload Page
                                </a>
                            </div>
                        </div>
                        
                        <iframe id="dashboard-frame" class="dashboard-frame" style="display: none;" 
                                sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"></iframe>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="fullscreen-container" class="fullscreen-container">
    <button id="exit-fullscreen-btn" class="fullscreen-toggle">
        <i class="fas fa-compress"></i> Exit Fullscreen
    </button>
    <iframe id="fullscreen-frame" class="dashboard-frame" 
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"></iframe>
</div>

{# The dashboard_template_html and actual_dataset_json are now passed via <script> in head_scripts block #}
{% endblock %}

{% block scripts %}
    {# Rename visual_generate.js to dashboard_renderer.js and include it here #}
    <script src="{{ url_for('static', filename='js/dashboard_renderer.js') }}" defer></script>
    {# visual.js might still be needed for general visual page interactions if any remain #}
    <script src="{{ url_for('static', filename='js/visual.js') }}" defer></script> 
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/welcome.html

```
{% extends "shared/base.html" %}

{% block content %}
<div class="flex flex-col items-center justify-center min-h-screen text-center px-4 space-y-8 pt-12">
    <h1 class="text-5xl font-extrabold text-blue-600">Say Hello to DynaDash!</h1>
    
    <p class="text-lg text-gray-700 max-w-3xl">
        Ever wished your data could tell its own story? With DynaDash, upload your private datasets and watch as Claude magically crafts eye-catching charts and insights. Curate your favourites, share them with friends, and explore data like never before—all in a flash!
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl w-full mx-auto">
    {% for feature in [
      { 'icon': '🔐', 'title': 'Secure Login',       'desc': 'Sign in to keep your data safe and personal.' },
      { 'icon': '📁', 'title': 'Easy Uploads',        'desc': 'Drag, drop or select CSV/JSON files in a snap.' },
      { 'icon': '🤖', 'title': 'Automated Charts',    'desc': 'Let Claude whip up visuals while you grab a coffee.' },
      { 'icon': '🔄', 'title': 'Live Updates',        'desc': 'Track processing in real time with Socket.IO.' },
      { 'icon': '🤝', 'title': 'Share & Collaborate', 'desc': 'Pick datasets or charts and share with your crew.' },
      { 'icon': '📱', 'title': 'Fully Responsive',    'desc': 'Looks great on any device, thanks to Tailwind CSS.' }
    ] %}
        <div class="relative group
                    bg-white rounded-2xl 
                    transform hover:-translate-y-1
                    transition-transform duration-300 
                    ring-0 hover:ring-4 hover:ring-pink-500/50
                    ring-offset-2 ring-offset-gray-900 
                    overflow-hidden
                    filter hover:drop-shadow-[0_0_10px_rgba(236,72,153,0.6)]"
        >
            <div class="h-32 flex items-center justify-center">
                <h2 class="text-2xl font-semibold group-hover:!text-pink-600 transition-colors duration-200">
                  {{ feature.icon }} {{ feature.title }}
                </h2>
            </div>
            <div
                class="absolute left-0 right-0 bottom-0
                       opacity-0 group-hover:opacity-100
                       transition-opacity duration-700 ease-in-out
                       px-6 pb-4
                       group-hover:delay-150
                       shadow-inner"
            >
                <p class="text-gray-300">
                   {{ feature.desc }}
                </p>
            </div>
        </div>
    {% endfor %}
    </div>
</div>
{% endblock %}

```

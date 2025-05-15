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
│   ├── 429.html
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


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/429.html

```
{% extends "errors/base_error.html" %}

{% set code = 429 %}
{% set title = "Too Many Requests" %}
{% set message = "You have made too many requests in a short period. Please wait a moment and try again." %}
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
                       class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('visual') %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
                          Visualizations
                    </a>
                    {# Use the new context function to check if data blueprint routes exist #}
                    {% if data_blueprint_exists_and_has_route('index') %}
                    <a href="{{ url_for('data.index') }}"
                      class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
                        Datasets 
                    </a>
                    {% endif %}
                    {% if data_blueprint_exists_and_has_route('upload') %}
                    <a href="{{ url_for('data.upload') }}"
                        class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint == 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
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
                            <span class="mr-2 text-text-color">{{ current_user.name }}</span>
                            <div class="relative">
                                <button type="button" id="user-menu-button" class="flex text-sm rounded-full focus:outline-none">
                                    <span class="sr-only">Open user menu</span>
                                    <div class="h-8 w-8 rounded-full flex items-center justify-center">
                                        {{ current_user.name[0] }}
                                    </div>
                                </button>
                            </div>
                            <div id="user-menu" class="hidden absolute right-0 top-full mt-2 w-48 rounded-md shadow-xl z-50 py-1 focus:outline-none" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
                                <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-sm" role="menuitem">Your Profile</a>
                                <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-sm" role="menuitem">Change Password</a>
                                <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-sm" role="menuitem">Sign out</a>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex space-x-4">
                        <a href="{{ url_for('auth.login') }}" class="px-3 py-2 rounded-md text-sm font-medium">Login</a>
                        <a href="{{ url_for('auth.register') }}" class="bg-magenta-primary px-3 py-2 rounded-md text-sm font-medium">Register</a>
                    </div>
                    {% endif %}
                </div>
                <div class="-mr-2 flex items-center sm:hidden">
                    <button type="button" id="mobile-menu-button" class="inline-flex items-center justify-center p-2 rounded-md focus:outline-none">
                        <span class="sr-only">Open main menu</span>
                        <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div id="mobile-menu" class="hidden sm:hidden">
            <div class="pt-2 pb-3 space-y-1 px-2">
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('visual.index') }}" class="{% if request.endpoint and request.endpoint == 'visual.index' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Visualizations
                </a>
                {% if data_blueprint_exists_and_has_route('index') %}
                <a href="{{ url_for('data.index') }}" class="{% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Datasets
                </a>
                {% endif %}
                {% if data_blueprint_exists_and_has_route('upload') %}
                <a href="{{ url_for('data.upload') }}" class="{% if request.endpoint and request.endpoint == 'data.upload' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Upload
                </a>
                {% endif %}
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Login
                </a>
                <a href="{{ url_for('auth.register') }}" class="block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Register
                </a>
                {% endif %}
            </div>
            {% if current_user.is_authenticated %}
            <div class="pt-4 pb-3 border-t">
                <div class="flex items-center px-4">
                    <div class="flex-shrink-0">
                        <div class="h-10 w-10 rounded-full flex items-center justify-center">
                            {{ current_user.name[0] }}
                        </div>
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium text-text-color">{{ current_user.name }}</div>
                        <div class="text-sm font-medium text-text-secondary">{{ current_user.email }}</div>
                    </div>
                </div>
                <div class="mt-3 space-y-1 px-2">
                    <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-base font-medium rounded-md">
                        Your Profile
                    </a>
                    <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-base font-medium rounded-md">
                        Change Password
                    </a>
                    <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-base font-medium rounded-md">
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
                        <span>{{ message }}</span>
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
            <div class="flex flex-col sm:flex-row justify-between items-center text-center sm:text-left">
                <div class="text-sm mb-2 sm:mb-0">
                    © {% block current_year %}2025{% endblock %} DynaDash. All rights reserved.
                </div>
                <div class="text-sm">
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
<div class="flex flex-col items-center justify-center py-16 px-4">
    <div class="text-6xl font-bold mb-4 text-danger">{{ error_code }}</div>
    <h1 class="text-3xl font-bold mb-6 text-center">{{ error_message }}</h1>
    
    <p class="mb-8 text-center max-w-lg">
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
    
    <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
        <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('visual.welcome') }}" class="btn w-full sm:w-auto">
            Go to Home
        </a>
        <button onclick="window.history.back()" class="btn btn-secondary w-full sm:w-auto">
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

{% block head_scripts %}
    {{ super() }}
    <!-- Font Awesome for icons (moved from bottom to ensure it's loaded before body) -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous" defer></script>
{% endblock %}


{% block content %}
<div class="flex flex-col items-center justify-center py-12 px-4">
    <h1 class="text-5xl font-bold mb-6 text-center">Welcome to DynaDash</h1>
    <p class="text-xl lead mb-8 text-center max-w-3xl">
        A web-based data-analytics platform that lets you upload datasets, 
        receive automated visualizations powered by Claude AI, and share insights with your team.
    </p>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl mb-12">
        <!-- Feature 1 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-upload"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Upload Datasets</h3>
            <p>
                Securely upload your CSV or JSON datasets and preview them instantly.
            </p>
        </div>
        
        <!-- Feature 2 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-chart-bar"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">AI-Powered Visualizations</h3>
            <p>
                Get automated exploratory analyses & visualizations generated by Claude AI.
            </p>
        </div>
        
        <!-- Feature 3 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-cubes"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Manage Your Gallery</h3>
            <p>
                Curate, annotate & manage visualizations in your personal gallery.
            </p>
        </div>
        
        <!-- Feature 4 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-share-alt"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Share Insights</h3>
            <p>
                Selectively share chosen datasets or charts with nominated peers.
            </p>
        </div>
    </div>
    
    {% if not current_user.is_authenticated %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('auth.register') }}" class="btn">
            Register Now
        </a>
        <a href="{{ url_for('auth.login') }}" class="btn btn-secondary">
            Login
        </a>
    </div>
    {% else %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('data.upload') }}" class="btn">
            Upload Dataset
        </a>
        <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
            View Visualizations
        </a>
    </div>
    {% endif %}
</div>

<!-- How It Works Section -->
<div class="bg-gray-50 py-16"> {# This bg-gray-50 will be themed by main.css #}
    <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">1. Upload Your Data</h3>
                <p class="mb-4">
                    Upload your CSV or JSON datasets securely to the platform. 
                    Our system validates your data and provides an instant preview.
                </p>
                <ul class="list-disc list-inside">
                    <li>Support for CSV and JSON formats</li>
                    <li>Secure file handling</li>
                    <li>Instant data preview</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Upload Interface Mockup</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 md:order-2 mb-8 md:mb-0 md:pl-8">
                <h3 class="text-2xl font-semibold mb-4">2. Generate Visualizations</h3>
                <p class="mb-4">
                    Our AI-powered system analyzes your data and generates meaningful visualizations 
                    automatically using Anthropic's Claude API.
                </p>
                <ul class="list-disc list-inside">
                    <li>AI-powered data analysis</li>
                    <li>Multiple chart types</li>
                    <li>Real-time progress tracking</li>
                </ul>
            </div>
            <div class="md:w-1/2 md:order-1">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Visualization Process Mockup</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">3. Share and Collaborate</h3>
                <p class="mb-4">
                    Curate your visualizations in a personal gallery and selectively share them 
                    with team members for collaboration.
                </p>
                <ul class="list-disc list-inside">
                    <li>Fine-grained access control</li>
                    <li>Personal visualization gallery</li>
                    <li>Team collaboration features</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Sharing Interface Mockup</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
{# Font Awesome script already moved to head_scripts for better practice #}
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
            <h1 class="text-3xl font-bold text-text-color">Generate Dashboard</h1>
            {# Ensure data.view exists or provide a fallback. text-blue-600 is themed to magenta by main.css #}
            <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else url_for('visual.index') }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Dataset
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Dataset Info Card -->
            <div class="md:col-span-1">
                {# .bg-white is themed to var(--card-bg) by main.css #}
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    {# .border-gray-200 is themed to var(--border-color) by main.css #}
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Dataset Details</h2>
                    </div>
                    <div class="p-4">
                        {# Changed text-gray-200 to text-text-color for better theme alignment #}
                        <h3 class="font-medium text-text-color mb-1">{{ dataset.original_filename }}</h3>
                        {# .text-gray-500 is themed to var(--text-secondary) by main.css #}
                        <p class="text-sm text-gray-500 mb-4">
                            {{ dataset.file_type.upper() }} • {{ dataset.n_rows }} rows • {{ dataset.n_columns }} columns
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Uploaded:</span> {{ dataset.uploaded_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Visibility:</span> 
                            {# text-green-600 for public status is fine, uses --accent-green via Tailwind #}
                            <span class="{{ 'text-green-600' if dataset.is_public else 'text-text-color' }}">
                                {{ 'Public' if dataset.is_public else 'Private' }}
                            </span>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Dashboard Form Card -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard Options</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.generate', dataset_id=dataset.id) }}" id="dashboard-form">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-4">
                                {# Rely on main.css for label styling; remove Tailwind classes #}
                                {{ form.title.label }}
                                <div class="mt-1">
                                    {# Rely on main.css for input styling; remove most Tailwind classes. Keep w-full if needed. #}
                                    {{ form.title(class="w-full", placeholder="Enter a title for your dashboard") }}
                                    {% if form.title.errors %}
                                        {# .text-red-500 is themed to var(--danger-light). Add invalid-feedback for potential icon/enhanced styling. #}
                                        <div class="invalid-feedback text-xs mt-1">
                                            {% for error in form.title.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                {{ form.description.label }}
                                <div class="mt-1">
                                    {{ form.description(class="w-full", rows=3, placeholder="Describe what insights you're looking for or what aspects of the data you want to highlight...") }}
                                    {% if form.description.errors %}
                                        <div class="invalid-feedback text-xs mt-1">
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
                                {# Use .alert .alert-info for the note box #}
                                <div class="alert alert-info">
                                    <span class="text-sm"> {# main.css alert styles will handle text color #}
                                        <strong>Note:</strong> Claude will analyze your dataset and automatically create a fully interactive dashboard with multiple visualizations. This process may take up to 60-90 seconds for larger datasets.
                                    </span>
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {# Use .btn class for the submit button #}
                                {{ form.submit(class="btn", value="Generate Dashboard", id="submit-button") }}
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Processing Modal -->
        <div id="processing-modal" class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
            {# Modal content uses CSS variables from main.css, which is good #}
            <div class="bg-card-bg rounded-lg shadow-lg p-6 max-w-md w-full border border-border-color">
                <h3 class="text-xl font-bold text-text-color mb-4">Generating Dashboard</h3>
                <div class="mb-4">
                    {# progress-container and #progress-bar are styled by main.css #}
                    <div class="progress-container">
                        <div id="progress-bar" style="width: 0%"></div>
                    </div>
                    <p id="progress-label" class="text-sm text-text-secondary mt-2">Initializing...</p>
                </div>
                <div class="text-text-secondary text-sm">
                    <p class="mb-2">Claude is analyzing your data and creating a custom dashboard. This may take 60-90 seconds to complete.</p>
                    {# steps-container and step-indicator are styled by main.css #}
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
                {# Use .alert .alert-danger for modal error message #}
                <div id="error-message-modal" class="mt-4 alert alert-danger error-message hidden">
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
                // Add 'step-active' for the current step based on percentage range
                let isActive = false;
                if (stepNum < Object.keys(steps).length) {
                     const nextStepPercent = steps[parseInt(stepNum) + 1] ? steps[parseInt(stepNum) + 1].percent : 100;
                     isActive = currentPercent >= step.percent && currentPercent < nextStepPercent;
                } else { // Last step
                     isActive = currentPercent >= step.percent;
                }

                if (currentPercent >= step.percent) {
                    indicatorEl.classList.remove('bg-gray-300'); // remove explicit tailwind class if present
                    indicatorEl.classList.add('step-completed');
                    textEl.classList.remove('text-text-tertiary');
                    textEl.classList.add('text-text-color'); // Or specific class for completed text
                    if (isActive) {
                        indicatorEl.classList.add('step-active');
                        textEl.classList.add('active'); // Assuming .active is styled in CSS
                    } else {
                         indicatorEl.classList.remove('step-active');
                         textEl.classList.remove('active');
                    }
                } else {
                     indicatorEl.classList.remove('step-completed', 'step-active');
                     // indicatorEl.classList.add('bg-gray-300'); // Not needed if default is styled by main.css
                     textEl.classList.remove('text-text-color', 'active');
                     textEl.classList.add('text-text-tertiary');
                }
            }
        }
    }


    if (dashboardForm && processingModal && progressBar && progressLabel) {
        dashboardForm.addEventListener('submit', function(event) {
            processingModal.classList.remove('hidden');
            progressBar.style.width = '0%';
            progressLabel.textContent = 'Initializing...';
            if(errorMessageModal) {
                 errorMessageModal.classList.add('hidden');
                 // Clear previous text if any, main.css might use :before for icon
                 errorMessageModal.textContent = 'An error occurred. Please try again or contact support if the problem persists.';
            }
            updateStepIndicator(0); 
        });
    }
});
</script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/index.html

```
{% extends "shared/base.html" %}

{% block title %}My Dashboards - DynaDash{% endblock %} {# Changed title slightly for clarity #}

{% block content %}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-text-color">My Dashboards</h1>
            {# Ensure the link to create new dashboard respects if data blueprint exists #}
            <a href="{{ url_for('data.upload') if data_blueprint_exists_and_has_route('upload') else '#' }}" class="btn">
                <i class="fas fa-plus mr-2"></i> Create New Dashboard
            </a>
        </div>

        {# Section for User's Own Dashboards (Paginated) #}
        {% if user_visualisations and user_visualisations.items %}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for vis in user_visualisations.items %}  {# Iterate through paginated items #}
                    <div class="bg-card-bg shadow-md rounded-lg overflow-hidden border border-border-color flex flex-col">
                        <div class="p-4 border-b border-border-color">
                            <h2 class="text-lg font-semibold text-text-color truncate" title="{{ vis.title }}">{{ vis.title }}</h2>
                        </div>
                        <div class="p-4 flex-grow">
                            {% if vis.description %}
                                <p class="text-sm text-text-secondary mb-3 h-16 overflow-hidden text-ellipsis">{{ vis.description }}</p>
                            {% else %}
                                <p class="text-sm text-text-tertiary mb-3 h-16 italic">No description provided.</p>
                            {% endif %}
                            <p class="text-xs text-text-tertiary">
                                Dataset: <span class="font-medium text-text-secondary">{{ vis.dataset.original_filename }}</span>
                            </p>
                            <p class="text-xs text-text-tertiary">
                                Created: <span class="font-medium text-text-secondary">{{ vis.created_at.strftime('%b %d, %Y %H:%M') }}</span>
                            </p>
                        </div>
                        <div class="p-4 bg-surface-1 border-t border-border-color flex justify-end space-x-2">
                            <a href="{{ url_for('visual.view', id=vis.id) }}" class="btn btn-secondary btn-sm">
                                <i class="fas fa-eye mr-1"></i> View
                            </a>
                            {# For user's own dashboards, vis.dataset.user_id will be current_user.id #}
                            <a href="{{ url_for('visual.share', id=vis.id) }}" class="btn btn-accent-green btn-sm">
                                <i class="fas fa-share-alt mr-1"></i> Share
                            </a>
                            <form action="{{ url_for('visual.delete', id=vis.id) }}" method="POST" class="inline m-0" onsubmit="return confirm('Are you sure you want to delete this dashboard?');">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                <button type="submit" class="btn btn-danger btn-sm">
                                    <i class="fas fa-trash-alt mr-1"></i> Delete
                                </button>
                            </form>
                        </div>
                    </div>
                {% endfor %}
            </div>
            
            {# Pagination for User's Own Dashboards #}
            {% if user_visualisations.has_prev or user_visualisations.has_next %}
            <div class="mt-8 flex justify-center">
                <nav aria-label="Pagination">
                    <ul class="inline-flex items-center -space-x-px shadow-sm">
                        {% if user_visualisations.has_prev %}
                        <li>
                            <a href="{{ url_for('visual.index', page=user_visualisations.prev_num) }}" class="btn btn-secondary btn-sm rounded-r-none">
                                <i class="fas fa-chevron-left mr-1"></i> Previous
                            </a>
                        </li>
                        {% endif %}
                        {% for page_num in user_visualisations.iter_pages(left_edge=1, right_edge=1, left_current=1, right_current=2) %}
                            {% if page_num %}
                                {% if user_visualisations.page == page_num %}
                                <li>
                                    <a href="#" class="btn btn-sm rounded-none" aria-current="page">{{ page_num }}</a>
                                </li>
                                {% else %}
                                <li>
                                    <a href="{{ url_for('visual.index', page=page_num) }}" class="btn btn-secondary btn-sm rounded-none">{{ page_num }}</a>
                                </li>
                                {% endif %}
                            {% else %}
                                <li><span class="btn btn-secondary btn-sm rounded-none disabled">...</span></li>
                            {% endif %}
                        {% endfor %}
                        {% if user_visualisations.has_next %}
                        <li>
                            <a href="{{ url_for('visual.index', page=user_visualisations.next_num) }}" class="btn btn-secondary btn-sm rounded-l-none">
                                Next <i class="fas fa-chevron-right ml-1"></i>
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
            </div>
            {% endif %}

        {% elif not shared_visualisations %} {# Only show "No Dashboards Yet" if BOTH lists are empty #}
             <div class="bg-card-bg border border-border-color rounded-lg p-12 text-center">
                <div class="text-text-tertiary text-5xl mb-4">
                    <i class="fas fa-chart-bar"></i>
                </div>
                <h2 class="text-2xl font-semibold text-text-color mb-3">No Dashboards Yet</h2>
                <p class="text-text-secondary mb-6">
                    It looks like you haven't created or been shared any dashboards.
                </p>
                <a href="{{ url_for('data.upload') if data_blueprint_exists_and_has_route('upload') else '#' }}" class="btn">
                    <i class="fas fa-plus mr-2"></i> Create Your First Dashboard
                </a>
            </div>
        {% endif %}

        {# Section for Dashboards Shared With Me #}
        {% if shared_visualisations %}
            <div class="mt-12"> {# Add some margin from the user's dashboards section #}
                <h2 class="text-2xl font-bold text-text-color mb-6">Shared With Me</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for vis_data in shared_visualisations %} {# Iterating through the list directly #}
                        <div class="bg-card-bg shadow-md rounded-lg overflow-hidden border border-border-color flex flex-col">
                            <div class="p-4 border-b border-border-color">
                                <h2 class="text-lg font-semibold text-text-color truncate" title="{{ vis_data.title }}">{{ vis_data.title }}</h2>
                            </div>
                            <div class="p-4 flex-grow">
                                {% if vis_data.description %}
                                    <p class="text-sm text-text-secondary mb-3 h-16 overflow-hidden text-ellipsis">{{ vis_data.description }}</p>
                                {% else %}
                                    <p class="text-sm text-text-tertiary mb-3 h-16 italic">No description provided.</p>
                                {% endif %}
                                <p class="text-xs text-text-tertiary">
                                    Dataset: <span class="font-medium text-text-secondary">{{ vis_data.dataset_filename }}</span>
                                </p>
                                <p class="text-xs text-text-tertiary">
                                    Owner: <span class="font-medium text-text-secondary">{{ vis_data.owner_name }}</span>
                                </p>
                                <p class="text-xs text-text-tertiary">
                                    Shared: <span class="font-medium text-text-secondary">{{ vis_data.created_at.strftime('%b %d, %Y %H:%M') }}</span> {# Using vis created_at #}
                                </p>
                            </div>
                            <div class="p-4 bg-surface-1 border-t border-border-color flex justify-end space-x-2">
                                <a href="{{ url_for('visual.view', id=vis_data.id) }}" class="btn btn-secondary btn-sm">
                                    <i class="fas fa-eye mr-1"></i> View
                                </a>
                                {# No share/delete for dashboards shared TO the user #}
                            </div>
                        </div>
                    {% endfor %}
                </div>
                {# You can add pagination for shared_visualisations here if it becomes a long list #}
                {# To do that, you'd need to paginate shared_visualisations_query in the route as well #}
            </div>
        {% endif %}

        {# Message if user has no personal dashboards but has shared ones #}
        {% if user_visualisations and not user_visualisations.items and shared_visualisations %}
            <div class="bg-card-bg border border-border-color rounded-lg p-12 text-center mt-8">
                 <h2 class="text-2xl font-semibold text-text-color mb-3">No Personal Dashboards</h2>
                <p class="text-text-secondary mb-6">
                    You haven't created any dashboards yet. You can see dashboards shared with you above.
                </p>
                 <a href="{{ url_for('data.upload') if data_blueprint_exists_and_has_route('upload') else '#' }}" class="btn">
                    <i class="fas fa-plus mr-2"></i> Create a Dashboard
                </a>
            </div>
        {% endif %}

    </div>
</div>
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/share.html

```
{% extends "shared/base.html" %}

{% block title %}Share Visualization - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-3xl font-bold text-text-color">Share Visualization</h1>
            {# text-blue-600 is themed to magenta by main.css #}
            <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Visualization
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Visualization Info Card -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Visualization Details</h2>
                    </div>
                    <div class="p-4">
                        {# Changed text-gray-200 to text-text-color #}
                        <h3 class="font-medium text-text-color mb-1">{{ visualisation.title }}</h3>
                        {% if visualisation.description %}
                            <p class="text-sm text-gray-500 mb-4">{{ visualisation.description }}</p>
                        {% endif %}
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Created:</span> {{ visualisation.created_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Dataset:</span> {{ dataset.original_filename }}
                        </p>
                        
                        <div class="mt-4 p-2 bg-surface-1 rounded"> {# Changed bg-gray-50 to bg-surface-1 #}
                            <div class="text-xs text-gray-500 mb-1">Preview:</div>
                            {# Changed bg-gray-100 to bg-surface-2 #}
                            <div class="h-32 flex items-center justify-center bg-surface-2 rounded">
                                <span class="text-text-tertiary text-sm">Visualization Preview</span> {# text-gray-400 themed to text-secondary, text-tertiary might be better #}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Share Form Card -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Share with Users</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.share', id=visualisation.id) }}">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-6">
                                {# Rely on main.css for label styling #}
                                {{ form.user_id.label }}
                                <div class="mt-1">
                                    {# Rely on main.css for select styling #}
                                    {{ form.user_id(class="w-full") }}
                                    {% if form.user_id.errors %}
                                        <div class="invalid-feedback text-xs mt-1">
                                            {% for error in form.user_id.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {# Use .btn class for submit #}
                                {{ form.submit(class="btn") }}
                            </div>
                        </form>
                        
                        <div class="mt-8">
                            <h3 class="text-lg font-medium text-text-color mb-4">Currently Shared With</h3>
                            
                            {% if shared_with %}
                                {# Table styling will be largely handled by main.css `table` selector #}
                                <div class="overflow-x-auto"> {# Wrapper for responsiveness #}
                                    <table class="min-w-full">
                                        <thead> {# Removed bg-gray-50, main.css table th has bg #}
                                            <tr>
                                                {# text-gray-500 themed to text-secondary #}
                                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    User
                                                </th>
                                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody> {# Removed bg-white and divide-y, main.css table handles this #}
                                            {% for user_share in shared_with %} {# Assuming shared_with is a list of User objects or similar #}
                                                <tr>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <div class="flex items-center">
                                                            {# Changed bg-gray-200 to bg-surface-3 for avatar placeholder #}
                                                            <div class="flex-shrink-0 h-10 w-10 bg-surface-3 rounded-full flex items-center justify-center">
                                                                <span class="text-text-color">{{ user_share.name[0] }}</span>
                                                            </div>
                                                            <div class="ml-4">
                                                                {# text-gray-900 themed to text-text-color #}
                                                                <div class="text-sm font-medium text-gray-900">
                                                                    {{ user_share.name }}
                                                                </div>
                                                                <div class="text-sm text-gray-500">
                                                                    {{ user_share.email }}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        {# text-red-600 themed to var(--danger). text-danger provided by main.css for links. #}
                                                        <form action="{{ url_for('visual.unshare', id=visualisation.id, user_id=user_share.id) }}" method="POST" class="inline">
                                                            <button type="submit" class="text-danger hover:text-danger-dark">
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
                                {# Changed bg-gray-50 to bg-surface-1 #}
                                <div class="bg-surface-1 rounded-lg p-6 text-center">
                                    <div class="text-text-tertiary text-4xl mb-3"> {# text-gray-400 themed to text-secondary, text-tertiary for icon #}
                                        <i class="fas fa-users-slash"></i>
                                    </div>
                                    {# text-gray-600 themed to text-secondary #}
                                    <p class="text-gray-600">
                                        This visualization is not shared with anyone yet.
                                    </p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                {# Use .alert .alert-info for the sharing information box #}
                <div class="mt-6 alert alert-info">
                    <h3 class="text-lg font-semibold mb-2">Sharing Information</h3> {# Alert styles will color this #}
                    <ul class="list-disc list-inside space-y-1"> {# Alert styles will color this #}
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
{# FontAwesome is usually included in base.html, but if not, keep it. #}
{# <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script> #}
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
        .dashboard-frame { width: 100%; height: 800px; min-height: 800px; border: none; background-color: var(--card-bg); } /* Changed background to var(--card-bg) */
        .dashboard-frame canvas { max-width: 100%; }
        .dashboard-container { height: auto; min-height: 800px; position: relative; width: 100%; }
        .fullscreen-toggle { position: absolute; top: 10px; right: 10px; z-index: 100; padding: 5px 10px; background-color: rgba(0,0,0,0.5); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .fullscreen-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background-color: var(--card-bg); display: none; } /* Changed background */
        .fullscreen-container .dashboard-frame { height: 100%; width: 100%; }
        .fullscreen-container .fullscreen-toggle { top: 20px; right: 20px; }
        .dashboard-error { padding: 20px; text-align: center; background-color: rgba(var(--danger-rgb), 0.1); border: 1px solid var(--danger); border-radius: var(--radius-md); margin: 20px 0; } /* Themed error box */
        .dashboard-error h3 { color: var(--danger); margin-bottom: 10px; }
        .dashboard-error p { color: var(--text-secondary); margin-bottom: 15px; } /* Themed paragraph */
        .dashboard-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; }
        .spinner { border: 4px solid var(--surface-3); width: 40px; height: 40px; border-radius: 50%; border-left-color: var(--magenta-primary); animation: spin 1s ease infinite; margin-bottom: 15px; } /* Themed spinner */
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .lg\:col-span-3 { width: 100%; }
    </style>
    <script>
        window.dynadashDatasetJson = {{ actual_dataset_json|safe }};
        window.dynadashDashboardTemplateHtml = {{ dashboard_template_html|tojson|safe }};
    </script>
{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-wrap justify-between items-center mb-6 gap-4"> {# Added flex-wrap and gap for responsiveness #}
            <div>
                <h1 class="text-3xl font-bold text-text-color">{{ visualisation.title }}</h1>
                {% if visualisation.description %}
                    <p class="text-text-secondary mt-1">{{ visualisation.description }}</p>
                {% endif %}
            </div>
            <div class="flex space-x-3 flex-wrap gap-2"> {# Added flex-wrap and gap for responsiveness #}
                <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left mr-1"></i> Back to Dashboards
                </a>
                
                {% if dataset.user_id == current_user.id %}
                    {# Assuming btn-success is green as per main.css themeing strategy #}
                    <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn btn-success">
                        <i class="fas fa-share-alt mr-1"></i> Share
                    </a>
                    
                    <form action="{{ url_for('visual.delete', id=visualisation.id) }}" method="POST" class="inline m-0">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        {# Assuming btn-danger is red #}
                        <button type="submit" class="btn btn-danger" 
                                onclick="return confirm('Are you sure you want to delete this dashboard? This action cannot be undone.');">
                            <i class="fas fa-trash-alt mr-1"></i> Delete
                        </button>
                    </form>
                {% endif %}
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="lg:col-span-1">
                {# Card uses direct CSS variables from main.css, which is good #}
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
                                {# text-magenta-primary is good use of CSS var #}
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
                            <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn btn-success w-full text-center">
                                <i class="fas fa-share-alt mr-1"></i> Share Dashboard
                            </a>
                        {% endif %}
                        
                        {# Assuming btn-accent-blue, btn-accent-purple, btn-accent-cyan are defined or bg-accent-* classes work correctly with .btn #}
                        <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="btn btn-accent-blue w-full text-center">
                            <i class="fas fa-database mr-1"></i> View Dataset
                        </a>
                        
                        <button id="fullscreen-btn" class="btn btn-accent-purple w-full text-center">
                            <i class="fas fa-expand mr-1"></i> Fullscreen Mode
                        </button>
                        
                        {# bg-gray-500 button changed to btn-secondary #}
                        <button id="download-btn-dashboard" class="btn btn-secondary w-full text-center">
                            <i class="fas fa-download mr-1"></i> Download HTML
                        </button>
                        
                        <button id="refresh-btn-dashboard" class="btn btn-accent-cyan w-full text-center">
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
                            <p>There was a problem displaying the dashboard. This may be due to browser security restrictions or a temporary issue.</p> {# Removed text-text-secondary as dashboard-error p handles color #}
                            <div>
                                <button id="reload-dashboard-btn" class="btn btn-accent-blue">
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
{% endblock %}

{% block scripts %}
    <script src="{{ url_for('static', filename='js/dashboard_renderer.js') }}" defer></script>
    <script src="{{ url_for('static', filename='js/visual.js') }}" defer></script> 
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/welcome.html

```
{% extends "shared/base.html" %}

{% block content %}
<div class="flex flex-col items-center justify-center min-h-screen text-center px-4 space-y-8 pt-12">
    {# text-blue-600 is themed to magenta by main.css, including text-shadow effects #}
    <h1 class="text-5xl font-extrabold text-blue-600">Say Hello to DynaDash!</h1>
    
    {# text-gray-700 is themed to text-secondary #}
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
        {# .bg-white is themed to var(--card-bg) #}
        {# Replaced Tailwind ring and drop-shadow with main.css themed shadow-glow on hover #}
        <div class="relative group
                    bg-white rounded-2xl 
                    transform hover:-translate-y-1
                    transition-transform duration-300 
                    ring-0 group-hover:shadow-glow-intense {# Use main.css glow #}
                    ring-offset-2 ring-offset-gray-900 {# ring-offset might need adjustment with shadow glow #}
                    overflow-hidden"
        >
            <div class="h-32 flex items-center justify-center">
                 {# group-hover:!text-pink-600 changed to group-hover:text-magenta-primary for consistency #}
                <h2 class="text-2xl font-semibold group-hover:text-magenta-primary transition-colors duration-200">
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
                {# text-gray-300 is a light gray, suitable on dark card. Corresponds to text-text-color-muted or lighter. #}
                <p class="text-text-color-muted"> 
                   {{ feature.desc }}
                </p>
            </div>
        </div>
    {% endfor %}
    </div>
</div>
{% endblock %}
```

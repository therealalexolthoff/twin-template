#Set Up

*** A Quick Note: The primary maintainer for this project has an issue with his Windows Laptop and can't currently verify Windows set up instructions. As soon as he can, he will add a Windows installation guide. ***

##Mac

If you have a Mac, this **should** be straightforward. 

### Installing Homebrew

Homebrew is a third party package manager for command line tools. If that sentence felt jargon heavy, just think of it like this:

Your computer uses software packages (applications) all the time. If you are reading this on Github, it means you are using a web browser, which is a software package that lets you browse the internet. 

Not all software packages are visibile like a web browsers. Many, including some you will use in this project, are only accessible via the command line, which on Mac is called the terminal.

Homebrew is just a tool that helps you install, update, and delete software packages that only work in the terminal.

Now, to install it, start by opening your terminal. If you've never done that before, open the Mac search, type in "Terminal" and open it.

Once you have the terminal in, visit https://brew.sh/, copy this line: 
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

and paste it into your terminal. Press enter, and when you are asked for your password, enter it. After this, the installation will proceed until it's finished.

### Installing UV

Now that we have our CLI Package Manager, we need to install our  Python System Manager, UV!

If you've never used UV, but you are familiar with pip, anaconda, or venv, think of it as a combination of all three, and more, but also way faster and more reliable. If you've never used any of those, don't worry about it. We'll explain what UV is doing as we go along.

For now, just type brew install uv into your terminal, and press enter. Homebrew will install uv. When it is finished, type `uv --version` to confirm.

### Setting Up Our IDE

We need a place to build and run our code, often called an IDE. In your terminl, type `brew install --cask visual-studio-code` and press enter. 

Now, close your terminal, open it again, and type `code .` .

When you press enter, it will open Visual Studio Code. Ignore what you see and close it. We'll open VSCode again later.

***Why not Cursor?***
Cursor is a great IDE, but it's somewhat more complicated than Visual Studio Code, especially on start up. If you prefer Cursor, be our guest. But we strongly recommend VSCode for this project.

### Setting Up Your Google Cloud Account

We'll be using Google Cloud to create the website where our AI Digital Twin can be accessed.

You can sign up for an account with a gmail address. Check [this link](https://cloud.google.com/free) to sign up. 

### Setting Up The Google Cloud CLI

Open your terminal.

Type `brew install --cask gcloud-cli`.

This will install the CLI package for managing your google cloud account. You'll need this to send the code you write on your computer to Google Cloud so that it can create the website where the public can access your digital twin.

On Day 3, you'll use this to set up your Google Cloud Platform account for deployment of the first version of your digital twin.


### Setting Up An OpenAI API Key

We need to access the AI that will power our digital twin through what is called an API. If you're not familiar with the concept of an API, we strongly recommend you [check out this video](https://www.youtube.com/watch?v=ByGJQzlzxQg).

There are many AI APIs, but we're going to advocate that you use OpenAI's API.

#### ***COST ALERT***

This is the one and only time you will definitely need to pay something for this project. You can pay as little as $5. 

*** Why do I need to pay? *** 
Companies that provide these AI APIs charge money every time you use them because they have to pay for electricity every time you use the API. While the amount they pay each time you use the API is tiny, it adds up quickly, and it's relatively easy to create software that automatically uses the API hundreds of times per minute. So while you may be using ChatGPT regularly for free, you are probably not sending hundreds of messages a minute. 

To manage and discourage this kind of overuse, the companies rely on metered pricing. That basically means you prepay an amount of money to the company, and then every time you use the API, they withdraw some of the money you paid them to cover their electricity costs for you using the API. This is an oversimplification, but it covers the core point. 

Now, you might be wondering *"Do I need to worry that I will spend my $5 very quickly?"* 

The answer is, unless you try really hard, or accidentally share your account information with the wrong person, that no, you will not spend the $5 quickly. In fact, it may take you 6 months or more to spend. If you're reading this, we're guessing you can spare $5 for that long of a time frame.

Now, to sign up, visit the [OpenAI Platform](https://platform.openai.com/login). We recommend you sign up with the same google account you used to sign up with GCP, just to keep things simple.

When you sign up, you will be asked to give your name and age. If you're reading this and you're under the age of 12, we'd like to stop a moment and acknowledge how cool and sophisticated you are. Some of us were playing with sticks in the forest at this age, and writing code was about as far away from our thoughts as possible.

*That being said*, this is not currently the project for you. OpenAI, and all other AI companies, limit access to children 13 and older. 

If you are 13-17, you're still pretty cool, but you're going to have to do the uncool thing and ask your parents for permission. This guide, unfortunately, does not cover that process.

For all of you who are 18+, go ahead and enter your age, followed by creating your project and naming your organization. None of this really matters right now, so just skip ahead to the pricing page.

Here's where we need to make something clear. You **can** use OpenAI's API for free, but not for this project. They do have a free tier now, but it is heavily restricted, and will not work for the project. If you want to try it anyway, or use some other API, feel free, but for best results, we recommend $5 to use OpenAI's API.

Once you've gotten the account set up, you'll need to create an API key.

** IMPORTANT ** API keys should never be displayed, shared, or stored unsafely. In the Day 1 guide for this project, we'll explain how you can protect your API key in a range of circumstances, but for now, just copy it from the OpenAI platform and save it in a file on your local computer that never touches the internet.


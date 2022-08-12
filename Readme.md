# About Restsh

Restsh is a shell-like command interpreter for working with RESTful (or REST-esque) remote services.

Often, when you're doing ad-hoc, exploratory, or emergency work with a service like that you're using curl, wget, or GUI interfaces, often in conjunction with some grepping, cutting, and pasting into new requests.

But what if instead, you could treat those service calls like simple functions, and their results and arguments like the data that they *are*?

Enter restsh, combining a shell-like experience for quick and dirty work, and a method for describing how a REST service works (parameter types and so on) so it can be used like a function. This allows you to easily combine, chain, repeat, and script different service calls.


## Sample Session

An example session, using the example outlook service to check emails in an outlook mailbox:

```
REST Shell 
 
Use the "help" command to get help, and "exit" to exit the shell. 
$ import outlook
$ help outlook.setAuthentication
outlook.setAuthentication is a function 
 
It takes 1 arguments: 
  auth: string 
 
$ outlook.setAuthentication(auth: "eyJ0eXAiOiJKV1Q....")
Service[outlook]
$ let messages = outlook.getMessages(mboxId: "me@example.com")
$ size(of: messages)
6
$ let getSender = \item. item.Sender.EmailAddress.Name
$ let senders = map(arr: messages, fn: getSender)
$ senders
[ "Steven", "Molly", "Mark", "Target", "Louise", "Campaign for Better Times" ]
$ exit
```

## Installation

To install you can either use the provided install.sh script, or from the top of the source directory, simply:

$ pip3 install .

# Basics

## Types

Restsh supports four simple types:

* strings

	* Strings are double quoted, like:
	
		`"Hello World!"`
	
	* Double quotes inside a string can be escaped with a `\`
	
		`"\"Learning programming,\" they said. \"It'll be fun,\" they said."`

* integers

	* Simple series of digits (in base 10), optionally starting with - or +

		`12`

		`007`

		`-15`

		`+32`

* floats
	
	* Like integers, but with a decimal point
	
		`12.5`

		`007.0`

		`-3.141592`

		`+0.1`

* booleans

	* True and false:
	
		`true`

		`false`

It supports two compound types:

* arrays

	* Defined by bracketing a series of values separated by commas
	
		`[1, "two", 3.0]`

	* Arrays support subscripts to select specific elements
	
		`myArray[1]`

* objects

	* Objects are like dictionaries and are defined by a series of key-value-pairs
	
		`{ color: "red", radius: 12 }`

While array elements and object properties may be modified, neither arrays nor
objects may be extended or shrunk after creation.

## Variables

Variables are declared with `let`, and can be assigned values with `=`.

	$ let pi
	$ pi = 3.14159 
	$ let tau = 6.28318

Assignment with `=` is a _statement_ and can only be used at the prompt or the top-level of scripts. To set the value of a variable within a function, for instance, use the `set` function.

	$ let foo = 2
	$ let setFoo = \to. set(var:foo, value: to)
	$ setFoo(to:4)
	4
	$ foo
	4

## Functions

Custom functions are defined like this:

	\foo, bar. foo + bar

where the above is a function that takes two arguments, `foo` and `bar`, and returns their sum. You might call it like
this:

	$ let sum = \foo, bar. foo + bar
	$ sum(foo: 5, bar: 3)
	8
	$ sum(bar: 3, foo: 5)
	8

Notice that the order of the arguments doesn't matter - just that they're named correctly. Built-in functions and service methods may also have specific type requirements for their arguments.

If you need to do more than one thing in a function, you can chain together expressions with `;`. The final expression will be result of the function.

## Handling errors

Most errors cancel execution of a command. However, if it's desirable to ignore an error, a `try` expression can be used to instead return `null` in case of an error.

	$ let num = 4
	$ let den = 0
	$ num / den
	error: ZeroDivisionError: division by zero
	$ try num / den
	error: ZeroDivisionError: division by zero
	null
	$ 

# Web Requests

Simple web requests can be made with the `http` object. `http`'s methods all take a complete URL, and return the text response of the request. On a non-2XX or 1XX response, an error is thrown with the status text of the response.

	$ http.get(url:"http://www.example.com")
	"<html><body><p>This domain is for use in illustrative examples in documents.</p></body></html>"
	$ 

For more complex requests, you will need to define a service.

# Services

Services are the heart of restsh. A service is an object with methods that make restful calls and return their result. Each service is defined by a YAML file. There are several examples included in the "example-services" directory.

A service can be added to the session with the `import` command

	$ import msgraph

The `import` command adds the ".yaml" extension to the service name specified to create the filename where the service is defined. To open the file, restsh first looks in the current directory, and then in the ~/.restsh directory.

After a service is imported, a new object with the service's name as added to the session. That object as a method for each call defined in its YAML file, plus the following predefined methods:

* `setHost(host)` - Replaces the host and port defined in the service definition

* `setAuthentication(auth)` - Sets or replaces the authentication data of the service. This persists between calls, but only is only used if the authentication type is set in the service definition.


## Defining Services

Service definitions are layed out as follows:

	---
	protocol: http|https|amqp
	host: host & port
	authentication:
	  type: basic|bearer
	  data: auth data string - for basic, separate user and password with a :
	call:
	  - name: method name
	    timeout: call timeout in seconds; 60 second default
	    params:
	      method-param1: data type
	      method-param2: data type
	    body: text of the request body, if any
	    response:
	      type: json|text
	      transform: restsh code
	      error: restsh code
	    # For http and https protocols:
	    path: path portion of the URL
	    query: query string portion of the URL	    
	    fragment: hash string portion of the URL

At the top-level, only `protocol`, `host`, and `call` are required. If the `authentication` section is omitted, no authentication will be done, even if you later call `setAuthentication` on the service object.

The `call` section is a list of service call definitions. Here, only the `name` property of a call is truly required.

The `params` section is a list of parameter names and types. The parameter names will be used for the service method's parameters, and as template variables for the text attributes of the call definition.

The `body` section will be sent as the data of the request.

For `http` and `https` requests, `path`, `query`, and `fragment` are combined with the `host` to create the URL to connect.

The `response` section defines how to handle the service response. By default the full text of th response is returned as a string, but the `type` can be used to interpret the `json` as a restsh object instead. The `transform` section allows you to specify a restsh command whose result replaces the default response object as the call method's result. Similarly, the `error` section is a restsh command whose result, if `true`, causes the call method to throw an error rather than return a result.

## Text Templates

The following call attributes allow for template variables:

* body
* path
* query
* fragment

Template variables are specified in text by surrounding any of the named call parameters in `$` characters. (To include a `$` in the text directly as `$$`.) The value of corresponding method argument will replace the template variable.

Take the following call definition on a service called `userprofile`:

	name: setDescription
	path: /profile
	method: PATCH
	params:
	  text: string
	body: |
	  { "description": "$text$"
	  }

This would be called from the shell like

	$ import userprofile
	$ userprofile.setDescription(text: "I love cats and rombic solids")
	"updated!"
	$

This call would send a PATCH request with the body

	{ "description": "I love cats and rombic solids"
	}

## Response Section

### type

The `type` attribute can be either `text`, in which case the response will be a string that is the entire response body, or `json` in which case the result will be parsed as JSON and the response type will depend on the content of the response itself.

### transform

The `transform` attribute is a restsh command. Within the transform command, every top level variable, function, and operator is available for use. In addition, the variable `response` is defined, containing the default service call response (dependant on the specified `type`).

Services using the `http` and `https` protocols additionally provide `status`, containing the HTTP status code of the response, and `headers` an object containing the response headers.

### error

The `error` attribute functions much the same as the `transform` attribute. However, the `error` command must return either `true`, if the response should be considered failed, or `false` if it was successful.

## AMQP Support

Restsh uses the amqp package for AMQP 0-9 support. However, it is not a hard
requirement. If you want to define AMQP-based services, you will need to
pip-install amqp separately.

Services using the `amqp` protocol only support `basic` authentication (or none).

# Scripting

On startup, restsh will look for a file named `~/.restshrc` and run all of the commands there before the first prompt. Additionally, you can direct restsh to run other script files before first prompt with the `--environment` command-line argument.

If other files are provided on the command-line, they will be run in order and then the interpreter will exit. This can be combined with `--environment` arguments.
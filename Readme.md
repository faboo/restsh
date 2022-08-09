# Basics

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

It also support custom functions, defined like this:

	\foo, bar. foo + bar

where the above is a function that takes two arguments, `foo` and `bar`, and returns their sum. You might call it like
this:

	$ let sum = \foo, bar. foo + bar
	$ sum(foo: 5, bar: 3)
	8
	$ sum(bar: 3, foo: 5)
	8

Notice that the order of the arguments doesn't matter - just that they're named correctly. Built-in functions and service methods may also have specific type requirements for their arguments.

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

## Handling errors

Most errors cancel execution of a command. However, if it's desirable to ignore an error, a `try` expression can be used to instead return `null` in case of an error.

	$ let num = 4
	$ let den = 0
	$ num / den
	error: ZeroDivisionError: division by zero
	$ try 4/0
	error: ZeroDivisionError: division by zero
	null
	$ 


# AMQP Support

Restsh uses the amqp package for AMQP 0-9 support. However, it is not a hard
requirement. If you want to define AMQP-based services, you will need to
pip-install amqp separately.

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
$
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

where the above is a function that takes two arguments, `foo` and `bar`, and returns their sum.


# AMQP Support

Restsh uses the amqp package for AMQP 0-9 support. However, it is not a hard
requirement. If you want to define AMQP-based services, you will need to
pip-install amqp separately.
